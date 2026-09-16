/* Analógico Domingo — app.js
   Navegación SPA (fragmentos), reproductor persistente y utilidades. */

var rpCache = new Map();
var rpNavCtrl = null;
var rpNavSeq = 0;
var rpPrefetchTimers = new WeakMap();
var rpDebounceTimers = new WeakMap();
var rpCargaMin = 300;
var rpCargaInicio = 0;
var rpCargaHideTimer = null;

var rpMain = document.querySelector("main");
if (rpMain) rpMain.setAttribute("tabindex", "-1");

/* ============================================================
   UTILIDADES UI
============================================================ */

function rpCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
}

function rpToast(mensaje) {
    var t = document.getElementById("rp-toast");
    if (!t) {
        t = document.createElement("div");
        t.id = "rp-toast";
        t.className = "toast";
        t.setAttribute("role", "status");
        document.body.appendChild(t);
    }
    t.textContent = mensaje;
    t.classList.add("visible");
    clearTimeout(t._tm);
    t._tm = setTimeout(function() { t.classList.remove("visible"); }, 2200);
}

function confirmEliminar(mensaje) {
    mensaje = mensaje || '¿Eliminar este elemento? Esta acción no se puede deshacer.';
    return window.confirm(mensaje);
}

/* ============================================================
   SUBIDA (Cloudinary / local) Y PREVIEW DE PORTADAS
============================================================ */

function rpSubirCloudinary(sig, file, onProgress) {
    return new Promise(function(resolve, reject) {
        var fd = new FormData();
        fd.append("file", file);
        fd.append("api_key", sig.api_key);
        fd.append("timestamp", sig.timestamp);
        fd.append("signature", sig.signature);
        fd.append("folder", sig.folder);
        fd.append("resource_type", "auto");

        var xhr = new XMLHttpRequest();
        xhr.open("POST", sig.upload_url);
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total * 100);
        };
        xhr.onload = function() {
            var data;
            try { data = JSON.parse(xhr.responseText); } catch (err) { return reject(new Error("Respuesta inválida del servidor")); }
            if (data.error) return reject(new Error(data.error.message || "Error de Cloudinary"));
            resolve(data.secure_url);
        };
        xhr.onerror = function() { reject(new Error("Error de red al subir el archivo")); };
        xhr.send(fd);
    });
}

function rpObtenerFirma(url) {
    return fetch(url).then(function(r) {
        if (!r.ok) throw new Error("Error obteniendo firma");
        return r.json();
    });
}

function rpSubirLocal(file, folder, onProgress) {
    return new Promise(function(resolve, reject) {
        var fd = new FormData();
        fd.append("file", file);
        fd.append("folder", folder);
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/musica/upload-local");
        xhr.setRequestHeader("X-CSRF-Token", rpCsrfToken());
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total * 100);
        };
        xhr.onload = function() {
            var data;
            try { data = JSON.parse(xhr.responseText); } catch (err) { return reject(new Error("Respuesta inválida del servidor")); }
            if (data.error) return reject(new Error(data.error));
            if (!data.url) return reject(new Error("No se recibió la URL de la portada"));
            resolve(data.url);
        };
        xhr.onerror = function() { reject(new Error("Error de red al subir la portada")); };
        xhr.send(fd);
    });
}

function rpPreviewPortada(inputId, imgId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    input.addEventListener("change", function() {
        var img = document.getElementById(imgId);
        if (input.files && input.files[0]) {
            if (img) {
                img.src = URL.createObjectURL(input.files[0]);
                img.style.display = "block";
                img.hidden = false;
            }
        }
    });
}

function rpInitFormularios() {
    var pares = [
        ["input-portada", "vista-previa-portada"]
    ];
    pares.forEach(function(p) {
        var input = document.getElementById(p[0]);
        if (input && !input._rpPreview) {
            input._rpPreview = true;
            rpPreviewPortada(p[0], p[1]);
        }
    });
}

/* ============================================================
   REPRODUCTOR PERSISTENTE
============================================================ */

var rpAudio = document.getElementById("rp-audio");
var rpBar = document.getElementById("reproductor");
var rpBtnPlay = document.getElementById("rp-btn-play");
var rpActual = document.getElementById("rp-actual");
var rpDuracion = document.getElementById("rp-duracion");
var rpTitulo = document.getElementById("rp-titulo");
var rpVolumenSlider = document.getElementById("rp-volumen");
var rpBarra = document.getElementById("rp-barra");
var rpBarraFill = document.getElementById("rp-barra-fill");
var rpBarraThumb = document.getElementById("rp-barra-thumb");
var rpDragging = false;
var rpPendienteReanudar = false;
var rpPortadaEl = document.getElementById("rp-portada");
var rpPortadaUrl = "";

if (rpAudio) rpAudio.volume = 0.8;

function rpFormato(segundos) {
    if (!isFinite(segundos)) return "0:00";
    var s = Math.max(0, Math.floor(segundos));
    var m = Math.floor(s / 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
}

function rpBarraPorcentaje(e) {
    var rect = rpBarra.getBoundingClientRect();
    var clientX = e.touches ? e.touches[0].clientX : e.clientX;
    var pct = ((clientX - rect.left) / rect.width) * 100;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    return pct;
}

function rpBarraActualizar() {
    if (!rpAudio.duration) return;
    var pct = (rpAudio.currentTime / rpAudio.duration) * 100;
    rpBarraFill.style.width = pct + "%";
    rpBarraThumb.style.left = pct + "%";
    rpActual.textContent = rpFormato(rpAudio.currentTime);
    rpBarra.setAttribute("aria-valuenow", Math.round(pct));
}

function rpBarraIr(e) {
    if (!rpAudio.duration) return;
    var pct = rpBarraPorcentaje(e);
    rpAudio.currentTime = (pct / 100) * rpAudio.duration;
    rpBarraActualizar();
}

function rpBarraDragStart(e) {
    e.preventDefault();
    rpDragging = true;
    rpBarraIr(e);
}

function rpBarraDragMove(e) {
    if (!rpDragging) return;
    rpBarraIr(e);
}

function rpBarraDragEnd() {
    rpDragging = false;
}

if (rpBarra) {
    rpBarra.addEventListener("mousedown", rpBarraDragStart);
    rpBarra.addEventListener("touchstart", rpBarraDragStart, {passive: false});
    document.addEventListener("mousemove", rpBarraDragMove);
    document.addEventListener("touchmove", rpBarraDragMove, {passive: false});
    document.addEventListener("mouseup", rpBarraDragEnd);
    document.addEventListener("touchend", rpBarraDragEnd);
}

function rpGuardar() {
    if (!rpAudio.src) return;
    try {
        localStorage.setItem("rp_state", JSON.stringify({
            src: rpAudio.src,
            titulo: rpTitulo.textContent,
            portada: rpPortadaUrl,
            currentTime: rpAudio.currentTime,
            playing: !rpAudio.paused,
            volume: rpAudio.volume
        }));
    } catch (e) {}
}

function rpSetPortada(url) {
    rpPortadaUrl = url || "";
    if (rpPortadaEl) {
        if (rpPortadaUrl) {
            rpPortadaEl.style.backgroundImage = "url('" + rpPortadaUrl + "')";
            rpPortadaEl.classList.add("tiene-portada");
            rpPortadaEl.textContent = "";
        } else {
            rpPortadaEl.style.backgroundImage = "";
            rpPortadaEl.classList.remove("tiene-portada");
            rpPortadaEl.textContent = "▶";
        }
    }
    rpActualizarActivos();
}

function rpRestore() {
    try {
        var state = JSON.parse(localStorage.getItem("rp_state"));
        if (!state || !state.src) return;
        if (!sessionStorage.getItem("rp_active")) return;
        rpTitulo.textContent = state.titulo || "---";
        rpSetPortada(state.portada);
        rpAudio.src = state.src;
        rpAudio.volume = state.volume !== undefined ? state.volume : 0.8;
        rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
        rpBar.style.display = "flex";
        rpAudio.addEventListener("loadedmetadata", function onLoad() {
            rpAudio.removeEventListener("loadedmetadata", onLoad);
            rpAudio.currentTime = state.currentTime || 0;
            if (state.playing) {
                rpAudio.play().catch(function() {
                    rpPendienteReanudar = true;
                });
            }
        });
    } catch(e) {}
}

rpAudio.addEventListener("timeupdate", function() {
    rpBarraActualizar();
});

rpAudio.addEventListener("loadedmetadata", function() {
    rpDuracion.textContent = rpFormato(rpAudio.duration);
    rpBarraActualizar();
});

rpAudio.addEventListener("play", function() {
    rpBtnPlay.textContent = "⏸";
    rpBtnPlay.setAttribute("aria-pressed", "true");
    rpActualizarActivos();
    rpGuardar();
});

rpAudio.addEventListener("pause", function() {
    rpBtnPlay.textContent = "▶";
    rpBtnPlay.setAttribute("aria-pressed", "false");
    rpPendienteReanudar = false;
    rpActualizarActivos();
    rpGuardar();
});

rpAudio.addEventListener("ended", function() {
    rpBtnPlay.textContent = "▶";
    rpBarraFill.style.width = "0%";
    rpBarraThumb.style.left = "0%";
    rpActual.textContent = "0:00";
    localStorage.removeItem("rp_state");
    sessionStorage.removeItem("rp_active");
    rpActualizarActivos();
    rpSiguiente();
});

function rpToggle() {
    if (!rpAudio.src) return;
    if (rpAudio.paused) {
        rpAudio.play();
    } else {
        rpAudio.pause();
    }
}

function rpSaltar(segundos) {
    if (!rpAudio.src || !rpAudio.duration) return;
    rpAudio.currentTime = Math.min(Math.max(rpAudio.currentTime + segundos, 0), rpAudio.duration);
    rpBarraActualizar();
    rpGuardar();
}

function rpVolumen(pct) {
    rpAudio.volume = pct / 100;
    rpGuardar();
}

function rpSiguiente() {
    var botones = [];
    rpMain.querySelectorAll("[data-play]").forEach(function(b) {
        var s = b.getAttribute("data-play");
        if (s && botones.indexOf(s) === -1) botones.push(s);
    });
    if (!botones.length) return false;
    var actual = rpAudio.src.replace(location.origin, "");
    var idx = botones.indexOf(actual);
    var sgte = (idx === -1) ? botones[0] : botones[(idx + 1) % botones.length];
    if (sgte === actual) return false;
    var btn = null;
    rpMain.querySelectorAll("[data-play]").forEach(function(b) {
        if (!btn && b.getAttribute("data-play") === sgte) btn = b;
    });
    if (!btn) return false;
    reproducirMusica(
        sgte,
        btn.getAttribute("data-titulo") || "Reproducción",
        btn.getAttribute("data-portada") || ""
    );
    return true;
}

function rpCerrar() {
    rpAudio.pause();
    rpAudio.src = "";
    rpBarraFill.style.width = "0%";
    rpBarraThumb.style.left = "0%";
    rpBar.style.display = "none";
    rpSetPortada("");
    localStorage.removeItem("rp_state");
    sessionStorage.removeItem("rp_active");
}

function reproducirMusica(url, titulo, portada) {
    var mismaCancion = rpAudio.src === url || rpAudio.src === location.origin + url;
    if (mismaCancion) {
        rpToggle();
        return;
    }
    rpTitulo.textContent = titulo;
    rpSetPortada(portada);
    rpAudio.src = url;
    rpBar.style.display = "flex";
    sessionStorage.setItem("rp_active", "1");
    rpAudio.play().catch(function() {
        rpPendienteReanudar = true;
    });
}

function rpEsActiva(url) {
    return rpAudio.src === url || rpAudio.src === location.origin + url;
}

function rpActualizarActivos() {
    var activos = document.querySelectorAll("[data-play].activa");
    activos.forEach(function(b) { b.classList.remove("activa"); b.innerHTML = "▶"; });
    activos = document.querySelectorAll("[data-play]");
    activos.forEach(function(b) {
        var src = b.getAttribute("data-play");
        if (rpEsActiva(src) && !rpAudio.paused) {
            b.classList.add("activa");
            b.innerHTML = "⏸";
        }
    });
}

document.addEventListener("click", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest("[data-play]") : null;
    if (!btn) return;
    e.preventDefault();
    var src = btn.getAttribute("data-play");
    var titulo = btn.getAttribute("data-titulo") || "Reproducción";
    var portada = btn.getAttribute("data-portada") || "";
    reproducirMusica(src, titulo, portada);
});

function compartir(url, titulo) {
    if (navigator.share) {
        navigator.share({ title: titulo, url: url }).catch(function() {});
    } else {
        rpToast('Copiando enlace…');
        navigator.clipboard.writeText(url).then(function() {
            rpToast('Enlace copiado al portapapeles');
        }).catch(function() {
            try { prompt('Copiá este enlace:', url); } catch (err) {}
            navigator.clipboard.writeText(url).then(function() {
                rpToast('Enlace copiado al portapapeles');
            }).catch(function() {
                rpToast('No se pudo copiar el enlace');
            });
        });
    }
}

async function compartirInstagram(imagenUrl, titulo, enlace) {
    if (imagenUrl) {
        try {
            var resp = await fetch(imagenUrl);
            if (resp.ok) {
                var blob = await resp.blob();
                var ext = (imagenUrl.split('?')[0].split('.').pop() || 'jpg').toLowerCase();
                var archivo = new File([blob], 'portada.' + ext, { type: blob.type || 'image/jpeg' });
                var datos = { files: [archivo] };
                if (navigator.canShare && navigator.canShare(datos)) {
                    await navigator.share(datos);
                    return;
                }
            }
        } catch (err) {
            if (err && err.name === 'AbortError') return;
        }
    }
    compartir(enlace, titulo);
}

function rpReintentarPlay() {
    if (!rpPendienteReanudar) return;
    if (!rpAudio.src || !rpAudio.paused) return;
    rpPendienteReanudar = false;
    rpAudio.play().catch(function() {});
}
document.addEventListener("pointerdown", rpReintentarPlay, true);
document.addEventListener("keydown", rpReintentarPlay, true);

/* ============================================================
   NAVEGACIÓN SPA (fragmentos + prefetch + cache)
============================================================ */

var rpExcluirAdmin = { login: true, logout: true, nuevo: true, editar: true, eliminar: true };

function rpEsNavegable(a) {
    if (!a) return false;
    if (a.target === "_blank" || a.hasAttribute("download")) return false;
    if (a.hasAttribute("data-play")) return false;
    var href = a.getAttribute("href");
    if (!href || href.charAt(0) === "#") return false;
    if (a.origin !== location.origin) return false;
    var segmentos = a.pathname.split("/").filter(Boolean);
    return !segmentos.some(function(s) { return rpExcluirAdmin[s]; });
}

function rpCacheGuardar(url, datos) {
    if (rpCache.size >= 40) {
        var clave = rpCache.keys().next().value;
        rpCache.delete(clave);
    }
    rpCache.set(url, datos);
}

function rpActualizarNav(url) {
    var ruta = new URL(url, location.origin).pathname;
    document.querySelectorAll("nav a").forEach(function(a) {
        var href = a.getAttribute("href");
        var activo;
        if (href === "/") {
            activo = (ruta === "/");
        } else {
            activo = ruta.indexOf(href) === 0;
        }
        a.classList.toggle("activo", activo);
    });
}

function rpMostrarCarga() {
    if (rpCargaHideTimer) {
        clearTimeout(rpCargaHideTimer);
        rpCargaHideTimer = null;
    }
    rpCargaInicio = performance.now();
    document.body.classList.add("cargando");
}

function rpOcultarCarga() {
    if (rpCargaHideTimer) return;
    var restante = rpCargaMin - (performance.now() - rpCargaInicio);
    if (restante <= 0) {
        document.body.classList.remove("cargando");
        return;
    }
    rpCargaHideTimer = setTimeout(function() {
        rpCargaHideTimer = null;
        document.body.classList.remove("cargando");
    }, restante);
}

function rpRender(datos, push, finalScroll) {
    var doc = new DOMParser().parseFromString(datos.html, "text/html");
    var nuevoMain = doc.querySelector("main");
    if (!nuevoMain) throw new Error("Sin <main>");

    rpMain.innerHTML = nuevoMain.innerHTML;
    rpMain.classList.remove("rp-fade-in");
    void rpMain.offsetWidth;
    rpMain.classList.add("rp-fade-in");

    rpActualizarActivos();
    rpInitFormularios();

    var titulo = doc.querySelector("title");
    if (titulo) document.title = titulo.textContent;

    rpActualizarNav(datos.finalUrl);

    if (push !== false) {
        history.pushState({ scrollY: window.scrollY }, "", datos.finalUrl);
        window.scrollTo(0, 0);
    } else {
        window.scrollTo(0, finalScroll);
    }

    rpMain.focus({ preventScroll: true });
}

function rpCargar(url, push, restaurarScroll) {
    if (rpNavCtrl) rpNavCtrl.abort();
    rpNavCtrl = new AbortController();
    var seq = ++rpNavSeq;
    var finalScroll = restaurarScroll || 0;
    rpMostrarCarga();

    var entrada = rpCache.get(url);
    if (entrada) {
        if (typeof entrada.then === "function") {
            entrada.then(function(datos) {
                if (seq !== rpNavSeq) return;
                rpOcultarCarga();
                try { rpRender(datos, push, finalScroll); } catch (e) { window.location.href = url; }
            }).catch(function() {
                if (seq !== rpNavSeq) return;
                rpOcultarCarga();
                window.location.href = url;
            });
            return;
        }
        try {
            rpRender(entrada, push, finalScroll);
        } catch (e) {
            window.location.href = url;
        }
        rpOcultarCarga();
        return;
    }

    fetch(url, {
        credentials: "same-origin",
        redirect: "follow",
        headers: { "X-Partial": "1" },
        signal: rpNavCtrl.signal,
        priority: "high"
    })
        .then(function(resp) {
            if (!resp.ok) throw new Error();
            return resp.text().then(function(html) {
                return { html: html, finalUrl: resp.url };
            });
        })
        .then(function(datos) {
            if (seq !== rpNavSeq) return;
            rpCacheGuardar(url, datos);
            if (datos.finalUrl && datos.finalUrl !== url) rpCacheGuardar(datos.finalUrl, datos);
            rpOcultarCarga();
            try {
                rpRender(datos, push, finalScroll);
            } catch (e) {
                window.location.href = url;
            }
        })
        .catch(function(err) {
            if (err && err.name === "AbortError") return;
            if (seq !== rpNavSeq) return;
            rpOcultarCarga();
            window.location.href = url;
        });
}

function rpPrefetch(url) {
    if (!url || url === location.href) return;
    if (rpCache.has(url)) return;
    fetch(url, {
        credentials: "same-origin",
        redirect: "follow",
        headers: { "X-Partial": "1" },
        priority: "low"
    })
        .then(function(resp) {
            if (!resp.ok) throw new Error();
            return resp.text().then(function(html) {
                return { html: html, finalUrl: resp.url };
            });
        })
        .then(function(datos) {
            rpCacheGuardar(url, datos);
            if (datos.finalUrl && datos.finalUrl !== url) rpCacheGuardar(datos.finalUrl, datos);
        })
        .catch(function() {});
}

function rpBuscarDiscos(valor) {
    valor = (valor || "").trim();
    var url = "/discos/";
    var params = [];
    if (valor) params.push("q=" + encodeURIComponent(valor));
    var select = document.getElementById("filtro-stock");
    var sval = select ? select.value : "";
    if (sval === "1" || sval === "0") params.push("stock=" + sval);
    var gselect = document.getElementById("filtro-genero");
    var gval = gselect ? gselect.value : "";
    if (gval) params.push("genero=" + encodeURIComponent(gval));
    if (params.length) url += "?" + params.join("&");
    rpCargar(url, true);
}

function rpLiveSearch(input) {
    clearTimeout(rpDebounceTimers.get(input));
    rpDebounceTimers.set(input, setTimeout(function() {
        if (document.activeElement && input.value !== document.activeElement.value) return;
        rpBuscarDiscos(input.value);
    }, 300));
}

document.addEventListener("click", function(e) {
    if (e.defaultPrevented) return;
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var objetivo = e.target;
    var enlace = objetivo && objetivo.closest ? objetivo.closest("a") : null;
    if (!enlace) return;
    if (!rpEsNavegable(enlace)) return;
    e.preventDefault();
    rpCargar(enlace.href, true);
});

if ("scrollRestoration" in history) history.scrollRestoration = "manual";

window.addEventListener("popstate", function() {
    var y = (history.state && typeof history.state.scrollY === "number") ? history.state.scrollY : 0;
    rpCargar(location.href, false, y);
});

document.addEventListener("submit", function(e) {
    var form = e.target;
    if (!form) return;

    if (form.id === "form-buscar") {
        var campo = form.querySelector('input[name="q"]');
        var valor = (campo && campo.value ? campo.value : "").trim();
        e.preventDefault();
        rpBuscarDiscos(valor);
        return;
    }

    if (form.id === "form-buscar-global") {
        var gcampo = form.querySelector('input[name="q"]');
        var gvalor = (gcampo && gcampo.value ? gcampo.value : "").trim();
        e.preventDefault();
        rpCargar("/buscar/?q=" + encodeURIComponent(gvalor), true);
    }
});

document.addEventListener("click", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest(".toggle-stock") : null;
    if (!btn) return;
    e.preventDefault();
    var id = btn.getAttribute("data-id");
    var nuevo = btn.classList.contains("badge-stock-no") ? 1 : 0;
    var fd = new FormData();
    fd.append("en_stock", nuevo);
    fetch("/discos/" + id + "/stock", { method: "POST", body: fd, credentials: "same-origin", headers: { "X-CSRF-Token": rpCsrfToken() } })
        .then(function(r) {
            if (!r.ok) throw new Error();
            return r.json();
        })
        .then(function(d) {
            btn.classList.toggle("badge-stock-si", d.en_stock === 1);
            btn.classList.toggle("badge-stock-no", d.en_stock !== 1);
            btn.textContent = d.en_stock ? "En stock" : "Sin stock";
        })
        .catch(function() {
            rpToast("No se pudo cambiar el stock");
        });
});

document.addEventListener("input", function(e) {
    var target = e.target;
    if (!target || target.id !== "buscar-discos") return;
    rpLiveSearch(target);
});

document.addEventListener("change", function(e) {
    var target = e.target;
    if (!target) return;

    if (target.id === "filtro-genero-peliculas") {
        var url = "/peliculas/";
        if (target.value) url += "?genero=" + encodeURIComponent(target.value);
        rpCargar(url, true);
        return;
    }

    if (target.id === "filtro-genero-musica") {
        var murl = "/musica/";
        if (target.value) murl += "?genero=" + encodeURIComponent(target.value);
        rpCargar(murl, true);
        return;
    }

    if (target.id !== "filtro-stock" && target.id !== "filtro-genero") return;
    var campo = document.getElementById("buscar-discos");
    var valor = campo && campo.value ? campo.value.trim() : "";
    rpBuscarDiscos(valor);
});

/* ============================================================
   PREFETCH por hover / touch
============================================================ */

document.addEventListener("pointerover", function(e) {
    var a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a || !rpEsNavegable(a)) return;
    clearTimeout(rpPrefetchTimers.get(a));
    rpPrefetchTimers.set(a, setTimeout(function() {
        rpPrefetch(a.href);
    }, 150));
}, true);

document.addEventListener("pointerdown", function(e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    var a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a || !rpEsNavegable(a)) return;
    clearTimeout(rpPrefetchTimers.get(a));
    rpPrefetch(a.href);
}, true);

/* ============================================================
   ATAJOS DE TECLADO
============================================================ */

document.addEventListener("keydown", function(e) {
    if (!rpAudio.src) return;
    var tag = (e.target && e.target.tagName) || "";
    var esCampo = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (e.target && e.target.isContentEditable);
    if (esCampo) return;

    switch (e.key) {
        case " ":
        case "k":
        case "K":
            e.preventDefault();
            rpToggle();
            break;
        case "ArrowUp":
            e.preventDefault();
            rpAudio.volume = Math.min(1, (rpAudio.volume || 0) + 0.05);
            rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
            rpGuardar();
            break;
        case "ArrowDown":
            e.preventDefault();
            rpAudio.volume = Math.max(0, (rpAudio.volume || 0) - 0.05);
            rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
            rpGuardar();
            break;
        case "ArrowLeft":
            e.preventDefault();
            rpAudio.currentTime = Math.max(0, (rpAudio.currentTime || 0) - 5);
            rpBarraActualizar();
            break;
        case "ArrowRight":
            e.preventDefault();
            if (rpAudio.duration) {
                rpAudio.currentTime = Math.min(rpAudio.duration, (rpAudio.currentTime || 0) + 5);
                rpBarraActualizar();
            }
            break;
        case "j":
        case "J":
            e.preventDefault();
            rpSaltar(-10);
            break;
        case "l":
        case "L":
            e.preventDefault();
            rpSaltar(10);
            break;
        case "n":
        case "N":
            e.preventDefault();
            rpSiguiente();
            break;
    }
});

/* ============================================================
   INICIALIZACIÓN
============================================================ */

function rpInitApp() {
    rpRestore();
    rpInitFormularios();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", rpInitApp);
} else {
    rpInitApp();
}
window.addEventListener("load", rpInitApp);
window.addEventListener("beforeunload", rpGuardar);
window.addEventListener("pagehide", rpGuardar);