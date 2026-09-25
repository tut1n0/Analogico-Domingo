/* Analógico Domingo — app.js
   Navegación SPA (fragmentos), reproductor persistente y utilidades. */

var rpCache = new Map();
var rpPendientes = new Map();
var rpNavCtrl = null;
var rpNavUrl = "";
var rpNavSeq = 0;
var rpPrefetchTimers = new WeakMap();
var rpDebounceTimers = new WeakMap();
var rpDiscosCacheVersion = 0;
var rpPreviewUrls = [];
var rpFlashTimer = null;
var rpEstado = window.__analogicoDomingoEstado || {
    inicializado: false,
    restaurado: false,
    listeners: []
};
if (!Array.isArray(rpEstado.listeners)) rpEstado.listeners = [];
window.__analogicoDomingoEstado = rpEstado;

function rpEscuchar(objetivo, tipo, clave, handler, opciones) {
    if (!objetivo || !handler) return;
    var existe = rpEstado.listeners.some(function(registro) {
        return registro.objetivo === objetivo && registro.tipo === tipo && registro.clave === clave;
    });
    if (existe) return;
    rpEstado.listeners.push({ objetivo: objetivo, tipo: tipo, clave: clave });
    objetivo.addEventListener(tipo, handler, opciones || false);
}

var rpMain = document.querySelector("main");
if (rpMain) rpMain.setAttribute("tabindex", "-1");

var rpHeader = document.querySelector("header");
var rpBarraCarga = document.getElementById("rp-barra-carga");
if (!rpBarraCarga) {
    rpBarraCarga = document.createElement("div");
    rpBarraCarga.id = "rp-barra-carga";
    if (rpHeader) rpHeader.appendChild(rpBarraCarga);
}

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

function rpAutoOcultarFlash() {
    clearTimeout(rpFlashTimer);
    rpFlashTimer = null;
    if (!rpMain) return;
    var flashes = rpMain.querySelectorAll(".flash-success-container");
    if (!flashes.length) return;
    rpFlashTimer = setTimeout(function() {
        flashes.forEach(function(flash) {
            flash.classList.add("flash-ocultando");
        });
        setTimeout(function() {
            flashes.forEach(function(flash) {
                if (flash.parentNode) flash.parentNode.removeChild(flash);
            });
        }, 500);
    }, 3000);
}

/* ============================================================
   SUBIDA (Cloudinary / local) Y PREVIEW DE PORTADAS
============================================================ */

function rpActualizarProgreso(contenedor, relleno, porcentaje) {
    if (!contenedor || !relleno) return;
    var valor = Number(porcentaje);
    if (!isFinite(valor)) return;
    valor = Math.min(100, Math.max(0, valor));
    relleno.style.width = valor + "%";
    contenedor.setAttribute("aria-valuenow", String(Math.round(valor)));
}

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

function rpRevocarObjectUrl(url) {
    if (!url || !window.URL || typeof window.URL.revokeObjectURL !== "function") return;
    try { window.URL.revokeObjectURL(url); } catch (e) {}
}

function rpRevocarPreviews() {
    var urls = rpPreviewUrls.slice();
    rpPreviewUrls = [];
    urls.forEach(rpRevocarObjectUrl);
}

function rpLiberarPreview(img) {
    if (!img || !img._rpPreviewUrl) return;
    var url = img._rpPreviewUrl;
    var indice = rpPreviewUrls.indexOf(url);
    img._rpPreviewUrl = "";
    if (indice !== -1) rpPreviewUrls.splice(indice, 1);
    rpRevocarObjectUrl(url);
}

function rpPreviewPortada(inputId, imgId) {
    var input = document.getElementById(inputId);
    if (!input) return;
    input._rpPreview = true;
    rpEscuchar(input, "change", "preview:" + inputId, function() {
        var img = document.getElementById(imgId);
        if (input.files && input.files[0]) {
            if (img) rpLiberarPreview(img);
            if (img && window.URL && typeof window.URL.createObjectURL === "function") {
                var url = window.URL.createObjectURL(input.files[0]);
                img._rpPreviewUrl = url;
                rpPreviewUrls.push(url);
                img.src = url;
                img.style.display = "block";
                img.hidden = false;
            }
        } else if (img) {
            rpLiberarPreview(img);
            img.removeAttribute("src");
            img.style.display = "";
            img.hidden = true;
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

    var progreso = document.getElementById("upload-progreso");
    var relleno = progreso ? progreso.querySelector(".upload-progreso-fill") : null;
    if (progreso && relleno) {
        progreso.setAttribute("role", "progressbar");
        progreso.setAttribute("aria-label", "Progreso de la subida");
        progreso.setAttribute("aria-valuemin", "0");
        progreso.setAttribute("aria-valuemax", "100");
        rpActualizarProgreso(progreso, relleno, parseFloat(relleno.style.width) || 0);
        if (!progreso._rpObservado && typeof window.MutationObserver === "function") {
            progreso._rpObservado = true;
            new window.MutationObserver(function() {
                rpActualizarProgreso(progreso, relleno, parseFloat(relleno.style.width) || 0);
            }).observe(relleno, { attributes: true, attributeFilter: ["style"] });
        }
    }
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

function rpMedirReproductor() {
    if (!rpBar) return;
    var visible = window.getComputedStyle(rpBar).display !== "none";
    var alto = visible ? Math.ceil(rpBar.getBoundingClientRect().height) : 0;
    document.documentElement.style.setProperty("--reproductor-espacio", alto + "px");
}

if (rpBar && typeof window.ResizeObserver === "function") {
    new window.ResizeObserver(rpMedirReproductor).observe(rpBar);
}
rpEscuchar(window, "resize", "reproductor:resize", rpMedirReproductor);

function rpFormato(segundos) {
    if (!isFinite(segundos)) return "0:00";
    var s = Math.max(0, Math.floor(segundos));
    var m = Math.floor(s / 60);
    return m + ":" + (s < 10 ? "0" : "") + s;
}

function rpBarraPorcentaje(e) {
    if (!rpBarra) return 0;
    var rect = rpBarra.getBoundingClientRect();
    var clientX = e.touches ? e.touches[0].clientX : e.clientX;
    var pct = ((clientX - rect.left) / rect.width) * 100;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    return pct;
}

function rpBarraActualizar() {
    var duracion = rpAudio && isFinite(rpAudio.duration) ? rpAudio.duration : 0;
    var actual = rpAudio && isFinite(rpAudio.currentTime) ? rpAudio.currentTime : 0;
    var pct = duracion ? (actual / duracion) * 100 : 0;
    if (pct < 0) pct = 0;
    if (pct > 100) pct = 100;
    if (rpBarraFill) rpBarraFill.style.width = pct + "%";
    if (rpBarraThumb) rpBarraThumb.style.left = pct + "%";
    if (rpActual) rpActual.textContent = rpFormato(actual);
    if (rpDuracion) rpDuracion.textContent = rpFormato(duracion);
    if (rpBarra) {
        rpBarra.setAttribute("aria-valuenow", Math.round(pct));
        rpBarra.setAttribute("aria-valuetext", rpFormato(actual) + " de " + rpFormato(duracion));
    }
}

function rpBarraIr(e) {
    if (!rpAudio || !rpBarra || !rpAudio.duration) return;
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

function rpBarraTeclado(e) {
    if (!rpAudio || !rpBarra || !rpAudio.duration) return;
    if (e.defaultPrevented || e.isComposing || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
    var actual = rpAudio.currentTime || 0;
    var siguiente = null;
    if (e.key === "Home") siguiente = 0;
    if (e.key === "End") siguiente = rpAudio.duration;
    if (e.key === "ArrowLeft") siguiente = Math.max(0, actual - 5);
    if (e.key === "ArrowRight") siguiente = Math.min(rpAudio.duration, actual + 5);
    if (siguiente === null) return;
    e.preventDefault();
    rpAudio.currentTime = siguiente;
    rpBarraActualizar();
    rpGuardar();
}

if (rpBarra) {
    rpEscuchar(rpBarra, "mousedown", "barra:mousedown", rpBarraDragStart);
    rpEscuchar(rpBarra, "touchstart", "barra:touchstart", rpBarraDragStart, {passive: false});
    rpEscuchar(rpBarra, "keydown", "barra:keydown", rpBarraTeclado);
    rpEscuchar(document, "mousemove", "barra:mousemove", rpBarraDragMove);
    rpEscuchar(document, "touchmove", "barra:touchmove", rpBarraDragMove, {passive: false});
    rpEscuchar(document, "mouseup", "barra:mouseup", rpBarraDragEnd);
    rpEscuchar(document, "touchend", "barra:touchend", rpBarraDragEnd);
}

function rpGuardar() {
    if (!rpAudio || !rpAudio.src) return;
    try {
        localStorage.setItem("rp_state", JSON.stringify({
            src: rpAudio.src,
            titulo: rpTitulo ? rpTitulo.textContent : "",
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
            rpPortadaEl.style.backgroundImage = "url(" + JSON.stringify(rpPortadaUrl) + ")";
            rpPortadaEl.classList.add("tiene-portada");
            rpPortadaEl.textContent = "";
        } else {
            rpPortadaEl.style.backgroundImage = "";
            rpPortadaEl.classList.remove("tiene-portada");
            rpPortadaEl.textContent = "";
        }
    }
    rpActualizarActivos();
}

function rpIntentarPlay() {
    if (!rpAudio || !rpAudio.src) return;
    var fuente = rpAudio.src;
    var resultado;
    try {
        resultado = rpAudio.play();
    } catch (e) {
        if (rpAudio.src === fuente) {
            rpPendienteReanudar = true;
            rpActualizarActivos();
        }
        return;
    }
    if (resultado && typeof resultado.then === "function") {
        resultado.then(function() {
            if (rpAudio.src === fuente) {
                rpPendienteReanudar = false;
                rpActualizarActivos();
            }
        }).catch(function() {
            if (rpAudio.src === fuente) {
                rpPendienteReanudar = true;
                rpActualizarActivos();
            }
        });
    } else {
        rpPendienteReanudar = false;
        rpActualizarActivos();
    }
}

function rpEsBoton(elemento) {
    if (!elemento) return false;
    var tag = (elemento.tagName || "").toUpperCase();
    var role = elemento.getAttribute && elemento.getAttribute("role");
    var tabindex = elemento.getAttribute && elemento.getAttribute("tabindex");
    return tag === "BUTTON" || (role && role.toLowerCase() === "button") || (tabindex !== null && tabindex !== undefined && parseInt(tabindex, 10) >= 0);
}

function rpActualizarControlPlay() {
    var reproduciendo = !!(rpAudio && rpAudio.src && !rpAudio.paused);
    var etiqueta = reproduciendo ? "Pausar" : "Reproducir";
    if (rpEsBoton(rpBtnPlay)) {
        rpBtnPlay.textContent = reproduciendo ? "⏸" : "▶";
        rpBtnPlay.setAttribute("aria-label", etiqueta);
        rpBtnPlay.setAttribute("title", etiqueta);
        rpBtnPlay.setAttribute("aria-pressed", reproduciendo ? "true" : "false");
    }
    if (rpEsBoton(rpPortadaEl)) {
        rpPortadaEl.setAttribute("aria-label", etiqueta);
        rpPortadaEl.setAttribute("aria-pressed", reproduciendo ? "true" : "false");
    }
}

function rpRestore() {
    if (rpEstado.restaurado) return;
    rpEstado.restaurado = true;
    try {
        var state = JSON.parse(localStorage.getItem("rp_state"));
        if (!state || !state.src) return;
        if (!sessionStorage.getItem("rp_active")) return;
        if (rpTitulo) rpTitulo.textContent = state.titulo || "---";
        rpSetPortada(state.portada);
        rpAudio.src = state.src;
        rpAudio.volume = state.volume !== undefined ? state.volume : 0.8;
        if (rpVolumenSlider) rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
        if (rpBar) rpBar.style.display = "flex";
        rpMedirReproductor();
        rpBarraActualizar();
        rpAudio.addEventListener("loadedmetadata", function onLoad() {
            rpAudio.removeEventListener("loadedmetadata", onLoad);
            rpAudio.currentTime = state.currentTime || 0;
            rpBarraActualizar();
            if (state.playing) rpIntentarPlay();
        });
    } catch(e) {}
    rpActualizarControlPlay();
}

rpEscuchar(rpAudio, "timeupdate", "audio:timeupdate", function() {
    rpBarraActualizar();
});

rpEscuchar(rpAudio, "loadedmetadata", "audio:loadedmetadata", function() {
    rpBarraActualizar();
});

rpEscuchar(rpAudio, "play", "audio:play", function() {
    rpPendienteReanudar = false;
    rpActualizarControlPlay();
    rpActualizarActivos();
    rpGuardar();
});

rpEscuchar(rpAudio, "pause", "audio:pause", function() {
    rpPendienteReanudar = false;
    rpActualizarControlPlay();
    rpActualizarActivos();
    rpGuardar();
});

rpEscuchar(rpAudio, "ended", "audio:ended", function() {
    rpPendienteReanudar = false;
    try { rpAudio.currentTime = 0; } catch (e) {}
    rpBarraActualizar();
    try { localStorage.removeItem("rp_state"); } catch (e) {}
    try { sessionStorage.removeItem("rp_active"); } catch (e) {}
    rpActualizarControlPlay();
    rpActualizarActivos();
    rpSiguiente();
});

function rpToggle() {
    if (!rpAudio || !rpAudio.src) return;
    if (rpAudio.paused) {
        rpIntentarPlay();
    } else {
        rpAudio.pause();
    }
}

function rpSaltar(segundos) {
    if (!rpAudio || !rpAudio.src || !rpAudio.duration) return;
    rpAudio.currentTime = Math.min(Math.max(rpAudio.currentTime + segundos, 0), rpAudio.duration);
    rpBarraActualizar();
    rpGuardar();
}

function rpVolumen(pct) {
    if (!rpAudio) return;
    var valor = Number(pct);
    if (!isFinite(valor)) return;
    rpAudio.volume = Math.min(1, Math.max(0, valor / 100));
    rpGuardar();
}

function rpSiguiente() {
    if (!rpAudio || !rpMain) return false;
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
    if (!rpAudio) return;
    rpAudio.pause();
    rpAudio.removeAttribute("src");
    try { rpAudio.load(); } catch (e) {}
    rpPendienteReanudar = false;
    rpBarraActualizar();
    if (rpBar) rpBar.style.display = "none";
    rpMedirReproductor();
    rpSetPortada("");
    try { localStorage.removeItem("rp_state"); } catch (e) {}
    try { sessionStorage.removeItem("rp_active"); } catch (e) {}
    rpActualizarControlPlay();
}

function reproducirMusica(url, titulo, portada) {
    if (!rpAudio || !url) return;
    var mismaCancion = rpAudio.src === url || rpAudio.src === location.origin + url;
    if (mismaCancion) {
        rpToggle();
        return;
    }
    if (rpTitulo) rpTitulo.textContent = titulo;
    rpSetPortada(portada);
    rpAudio.src = url;
    if (rpBar) rpBar.style.display = "flex";
    rpMedirReproductor();
    try { sessionStorage.setItem("rp_active", "1"); } catch (e) {}
    rpBarraActualizar();
    rpActualizarControlPlay();
    rpIntentarPlay();
}

function rpEsActiva(url) {
    if (!rpAudio) return false;
    return rpAudio.src === url || rpAudio.src === location.origin + url;
}

function rpActualizarActivos() {
    var reproduciendo = !!(rpAudio && rpAudio.src && !rpAudio.paused);
    document.querySelectorAll("[data-play]").forEach(function(b) {
        if (b._rpContenidoOriginal === undefined) b._rpContenidoOriginal = b.innerHTML;
        if (b._rpNombreOriginal === undefined) {
            b._rpNombreOriginal = b.getAttribute("data-titulo") || b.getAttribute("aria-label") || "Pista";
        }
        var activa = reproduciendo && rpEsActiva(b.getAttribute("data-play"));
        b.classList.toggle("activa", activa);
        b.innerHTML = activa ? "⏸" : b._rpContenidoOriginal;
        if (rpEsBoton(b)) {
            b.setAttribute("aria-label", (activa ? "Pausar" : "Escuchar") + " " + b._rpNombreOriginal);
            b.setAttribute("aria-pressed", activa ? "true" : "false");
        }
    });
    rpActualizarControlPlay();
}

rpEscuchar(document, "click", "click:play", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest("[data-play]") : null;
    if (!btn) return;
    e.preventDefault();
    var src = btn.getAttribute("data-play");
    var titulo = btn.getAttribute("data-titulo") || "Reproducción";
    var portada = btn.getAttribute("data-portada") || "";
    reproducirMusica(src, titulo, portada);
});

function rpCopiarExecCommand(texto) {
    return new Promise(function(resolve, reject) {
        var area = null;
        var activo = document.activeElement;
        try {
            if (!document.body || typeof document.execCommand !== "function") throw new Error("Clipboard no disponible");
            area = document.createElement("textarea");
            area.value = texto;
            area.setAttribute("readonly", "");
            area.style.position = "fixed";
            area.style.opacity = "0";
            document.body.appendChild(area);
            area.focus();
            area.select();
            if (!document.execCommand("copy")) throw new Error("No se pudo copiar");
            resolve();
        } catch (e) {
            reject(e);
        } finally {
            if (area && area.parentNode) area.parentNode.removeChild(area);
            if (activo && typeof activo.focus === "function") activo.focus();
        }
    });
}

function rpCopiarTexto(texto) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        try {
            return navigator.clipboard.writeText(texto).catch(function() {
                return rpCopiarExecCommand(texto);
            });
        } catch (e) {
            return rpCopiarExecCommand(texto);
        }
    }
    return rpCopiarExecCommand(texto);
}

function compartir(url, titulo) {
    if (typeof navigator.share === "function") {
        try {
            Promise.resolve(navigator.share({ title: titulo, url: url })).catch(function() {});
            return;
        } catch (e) {}
    }
    rpToast('Copiando enlace…');
    rpCopiarTexto(url).then(function() {
        rpToast('Enlace copiado al portapapeles');
    }).catch(function() {
        var mostrado = false;
        try {
            if (typeof window.prompt === "function") {
                mostrado = window.prompt('Copiá este enlace:', url) !== null;
            }
        } catch (err) {}
        if (mostrado) {
            rpToast('Copiá el enlace manualmente');
        } else {
            rpToast('No se pudo copiar el enlace');
        }
    });
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

rpEscuchar(document, "click", "click:instagram", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest("[data-compartir-instagram]") : null;
    if (!btn) return;
    e.preventDefault();
    compartirInstagram(
        btn.getAttribute("data-imagen") || "",
        btn.getAttribute("data-titulo") || "",
        btn.getAttribute("data-url") || location.href
    );
});

rpEscuchar(document, "click", "click:compartir", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest("[data-compartir]") : null;
    if (!btn) return;
    e.preventDefault();
    compartir(
        btn.getAttribute("data-url") || location.href,
        btn.getAttribute("data-titulo") || ""
    );
});

function rpReintentarPlay(e) {
    if (e && e.target && e.target.closest && e.target.closest("[data-play]")) return;
    if (e && e.type === "keydown" && (e.defaultPrevented || e.isComposing || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey || rpEsControlInteractivo(e.target))) return;
    if (!rpPendienteReanudar) return;
    if (!rpAudio || !rpAudio.src || !rpAudio.paused) return;
    rpPendienteReanudar = false;
    rpIntentarPlay();
}
rpEscuchar(document, "pointerdown", "play:retry-pointer", rpReintentarPlay, true);
rpEscuchar(document, "keydown", "play:retry-key", rpReintentarPlay, true);

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
    return !segmentos.some(function(s) {
        return Object.prototype.hasOwnProperty.call(rpExcluirAdmin, s);
    });
}

function rpNormalizarUrl(url) {
    try { return new URL(url, location.href).href; } catch (e) { return url; }
}

function rpEsUrlDiscos(url) {
    try {
        var ruta = new URL(url, location.href).pathname;
        return ruta === "/discos" || ruta.indexOf("/discos/") === 0;
    } catch (e) {
        return false;
    }
}

function rpCacheGuardar(url, datos) {
    if (rpCache.size >= 40 && !rpCache.has(url)) {
        var clave = rpCache.keys().next().value;
        rpCache.delete(clave);
    }
    rpCache.set(url, datos);
}

function rpPendienteActual(url) {
    var entrada = rpPendientes.get(url);
    if (!entrada) return null;
    if (rpEsUrlDiscos(url) && entrada.version !== rpDiscosCacheVersion) return null;
    if (entrada.signal && entrada.signal.aborted) return null;
    return entrada;
}

function rpInvalidarCacheDiscos() {
    rpDiscosCacheVersion++;
    rpCache.forEach(function(datos, url) {
        if (rpEsUrlDiscos(url)) rpCache.delete(url);
    });
}

function rpSolicitarParcial(url, signal, prioridad) {
    var version = rpDiscosCacheVersion;
    var opciones = {
        credentials: "same-origin",
        redirect: "follow",
        headers: { "X-Partial": "1" },
        priority: prioridad || "high"
    };
    if (signal) opciones.signal = signal;

    var peticion = fetch(url, opciones)
        .then(function(resp) {
            if (!resp.ok) throw new Error();
            return resp.text().then(function(html) {
                return { html: html, finalUrl: resp.url };
            });
        })
        .then(function(datos) {
            var finalUrl = rpNormalizarUrl(datos.finalUrl || url);
            var discoActual = version === rpDiscosCacheVersion;
            var discoDestino = rpEsUrlDiscos(url) || rpEsUrlDiscos(finalUrl);
            if (discoActual || !discoDestino) {
                rpCacheGuardar(url, datos);
                if (finalUrl !== url) rpCacheGuardar(finalUrl, datos);
            }
            return datos;
        });

    var entrada = { peticion: peticion, version: version, signal: signal };
    rpPendientes.set(url, entrada);
    peticion.then(function() {
        if (rpPendientes.get(url) === entrada) rpPendientes.delete(url);
    }, function() {
        if (rpPendientes.get(url) === entrada) rpPendientes.delete(url);
    });
    return entrada;
}

function rpActualizarNav(url) {
    var ruta = new URL(url, location.origin).pathname.replace(/\/+$/, "") || "/";
    document.querySelectorAll("nav a").forEach(function(a) {
        var href = a.getAttribute("href") || "";
        var rutaEnlace = href.replace(/\/+$/, "") || "/";
        var activo;
        if (rutaEnlace === "/") {
            activo = (ruta === "/");
        } else {
            activo = ruta === rutaEnlace || ruta.indexOf(rutaEnlace + "/") === 0;
        }
        a.classList.toggle("activo", activo);
        if (activo) {
            a.setAttribute("aria-current", "page");
        } else {
            a.removeAttribute("aria-current");
        }
    });
}

function rpMostrarCarga() {
    document.body.classList.add("cargando");
    if (rpMain) rpMain.setAttribute("aria-busy", "true");
}

function rpOcultarCarga() {
    document.body.classList.remove("cargando");
    if (rpMain) rpMain.setAttribute("aria-busy", "false");
}

function rpAplicarHistorial(url, modo, finalScroll) {
    if (modo === "push") {
        history.pushState({ scrollY: window.scrollY }, "", url);
        window.scrollTo(0, 0);
    } else if (modo === "replace") {
        var state = history.state || {};
        state.scrollY = window.scrollY;
        history.replaceState(state, "", url);
    } else {
        window.scrollTo(0, finalScroll);
    }
}

function rpCopiarAtributos(origen, destino) {
    while (destino.attributes.length) destino.removeAttribute(destino.attributes[0].name);
    for (var i = 0; i < origen.attributes.length; i++) {
        destino.setAttribute(origen.attributes[i].name, origen.attributes[i].value);
    }
}

function rpClaveMeta(meta) {
    return meta.getAttribute("property") || meta.getAttribute("name") || meta.getAttribute("http-equiv") || "";
}

function rpMetaDinamica(clave) {
    clave = (clave || "").toLowerCase();
    return clave === "csrf-token" || clave === "description" || clave.indexOf("og:") === 0 || clave.indexOf("twitter:") === 0;
}

function rpBuscarMeta(clave) {
    var resultado = null;
    document.head.querySelectorAll("meta").forEach(function(meta) {
        if (!resultado && rpClaveMeta(meta) === clave) resultado = meta;
    });
    return resultado;
}

function rpSincronizarHead(doc) {
    var titulo = doc.querySelector("title");
    if (titulo) document.title = titulo.textContent;
    if (doc.documentElement && doc.documentElement.lang) document.documentElement.lang = doc.documentElement.lang;

    var head = doc.head || doc.querySelector("head");
    if (!head) return;
    var canonical = head.querySelector('link[rel="canonical"]');
    var canonicalActual = document.head.querySelector('link[rel="canonical"]');
    if (canonical && canonicalActual) {
        rpCopiarAtributos(canonical, canonicalActual);
    } else if (canonical) {
        document.head.appendChild(canonical.cloneNode(true));
    }
    var metas = head.querySelectorAll("meta");
    if (!metas.length) return;
    if (!canonical && canonicalActual) canonicalActual.remove();
    var claves = Object.create(null);
    metas.forEach(function(meta) {
        var clave = rpClaveMeta(meta);
        if (clave && !claves[clave]) claves[clave] = meta;
    });

    metas.forEach(function(meta) {
        var clave = rpClaveMeta(meta);
        if (!clave) return;
        var actual = rpBuscarMeta(clave);
        if (actual) {
            rpCopiarAtributos(meta, actual);
        } else {
            document.head.appendChild(meta.cloneNode(true));
        }
    });

    document.head.querySelectorAll("meta").forEach(function(meta) {
        var clave = rpClaveMeta(meta);
        if (clave && !claves[clave] && rpMetaDinamica(clave)) meta.remove();
    });
}

function rpRender(datos, push, finalScroll, opciones) {
    opciones = opciones || {};
    var modo = opciones.historial || (typeof push === "string" ? push : (push === false ? "ninguno" : "push"));
    var doc = new DOMParser().parseFromString(datos.html, "text/html");
    var nuevoMain = doc.querySelector("main");
    if (!nuevoMain) throw new Error("Sin <main>");

    rpRevocarPreviews();
    rpMain.innerHTML = nuevoMain.innerHTML;
    rpMain.classList.remove("rp-fade-in");
    void rpMain.offsetWidth;
    rpMain.classList.add("rp-fade-in");

    rpActualizarActivos();
    rpInitFormularios();
    rpAutoOcultarFlash();
    rpSincronizarHead(doc);
    rpActualizarNav(datos.finalUrl || location.href);
    rpAplicarHistorial(datos.finalUrl || location.href, modo, finalScroll);

    if (!opciones.preservarFoco) rpMain.focus({ preventScroll: true });
}

function rpRenderResultadosDiscos(datos, modo, finalScroll, opciones) {
    opciones = opciones || {};
    var doc = new DOMParser().parseFromString(datos.html, "text/html");
    var form = document.getElementById("form-buscar");
    var nuevoForm = doc.querySelector("#form-buscar");
    if (!form || !nuevoForm) throw new Error("Sin formulario de discos");

    var padre = form.parentNode;
    var sibling = form.nextSibling;
    while (sibling) {
        var siguiente = sibling.nextSibling;
        padre.removeChild(sibling);
        sibling = siguiente;
    }

    sibling = nuevoForm.nextSibling;
    while (sibling) {
        var nuevoSiguiente = sibling.nextSibling;
        padre.appendChild(sibling);
        sibling = nuevoSiguiente;
    }

    rpActualizarActivos();
    rpInitFormularios();
    rpAutoOcultarFlash();
    rpSincronizarHead(doc);
    rpActualizarNav(datos.finalUrl || location.href);
    rpAplicarHistorial(datos.finalUrl || location.href, modo || "replace", finalScroll);

    var input = opciones.input;
    if (opciones.preservarFoco && input && document.activeElement === input && input.value === opciones.textoEnviado) {
        try { input.setSelectionRange(opciones.seleccionInicio, opciones.seleccionFin, opciones.seleccionDireccion); } catch (e) {}
    }
}

function rpCargar(url, push, restaurarScroll, opciones) {
    opciones = opciones || {};
    url = rpNormalizarUrl(url);
    var pendiente = rpPendienteActual(url);
    var modo = opciones.historial || (push === false ? "ninguno" : "push");
    var finalScroll = typeof restaurarScroll === "number" ? restaurarScroll : 0;
    var render = opciones.render || rpRender;

    if (rpNavCtrl && rpNavUrl !== url) rpNavCtrl.abort();
    if (!rpNavCtrl || rpNavCtrl.signal.aborted || rpNavUrl !== url) {
        rpNavCtrl = new AbortController();
        rpNavUrl = url;
    }

    var seq = ++rpNavSeq;
    var entrada = rpCache.get(url);
    if (entrada) {
        if (typeof entrada.then === "function") {
            entrada.then(function(datos) {
                if (seq !== rpNavSeq) return;
                rpCache.set(url, datos);
                rpOcultarCarga();
                try { render(datos, modo, finalScroll, opciones); } catch (e) { window.location.href = url; }
            }, function() {
                if (seq !== rpNavSeq) return;
                rpOcultarCarga();
                window.location.href = url;
            });
            return;
        }
        rpOcultarCarga();
        try { render(entrada, modo, finalScroll, opciones); } catch (e) { window.location.href = url; }
        return;
    }

    rpMostrarCarga();
    if (!pendiente) pendiente = rpSolicitarParcial(url, rpNavCtrl.signal, "high");
    pendiente.peticion.then(function(datos) {
        if (seq !== rpNavSeq) return;
        rpOcultarCarga();
        try {
            render(datos, modo, finalScroll, opciones);
        } catch (e) {
            window.location.href = url;
        }
    }, function(err) {
        if (err && err.name === "AbortError") return;
        if (seq !== rpNavSeq) return;
        rpOcultarCarga();
        window.location.href = url;
    });
}

function rpPrefetch(url) {
    if (!url) return;
    url = rpNormalizarUrl(url);
    if (url === location.href || rpCache.has(url) || rpPendienteActual(url)) return;
    var entrada = rpSolicitarParcial(url, null, "low");
    entrada.peticion.catch(function() {});
}

function rpUrlFiltrosPeliculas() {
    var form = document.getElementById("form-filtrar-peliculas");
    if (!form) return "/peliculas/";

    var params = [];
    var genero = form.querySelector('[name="genero"]');
    var decada = form.querySelector('[name="decada"]');
    if (genero && genero.value) params.push("genero=" + encodeURIComponent(genero.value));
    if (decada && decada.value) params.push("decada=" + encodeURIComponent(decada.value));

    return "/peliculas/" + (params.length ? "?" + params.join("&") : "");
}

function rpBuscarDiscos(valor, input) {
    var texto = valor || "";
    valor = texto.trim();
    var url = "/discos/";
    var params = [];
    if (valor) params.push("q=" + encodeURIComponent(valor));
    var select = document.getElementById("filtro-stock");
    var sval = select ? select.value : "";
    if (sval === "1" || sval === "0") params.push("stock=" + sval);
    var gselect = document.getElementById("filtro-genero");
    var gval = gselect ? gselect.value : "";
    if (gval) params.push("genero=" + encodeURIComponent(gval));
    var dselect = document.getElementById("filtro-decada");
    var dval = dselect ? dselect.value : "";
    if (dval) params.push("decada=" + encodeURIComponent(dval));
    if (params.length) url += "?" + params.join("&");
    var opciones = {
        historial: "replace",
        render: rpRenderResultadosDiscos,
        preservarFoco: !!input,
        input: input,
        textoEnviado: texto
    };
    if (input) {
        opciones.seleccionInicio = input.selectionStart;
        opciones.seleccionFin = input.selectionEnd;
        opciones.seleccionDireccion = input.selectionDirection;
    }
    rpCargar(url, false, window.scrollY, opciones);
}

function rpLiveSearch(input) {
    clearTimeout(rpDebounceTimers.get(input));
    rpDebounceTimers.set(input, setTimeout(function() {
        if (!document.documentElement.contains(input)) return;
        rpBuscarDiscos(input.value, input);
    }, 300));
}

rpEscuchar(document, "click", "nav:click", function(e) {
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

rpEscuchar(window, "popstate", "nav:popstate", function() {
    var y = (history.state && typeof history.state.scrollY === "number") ? history.state.scrollY : 0;
    rpCargar(location.href, false, y);
});

rpEscuchar(document, "submit", "nav:submit", function(e) {
    var form = e.target;
    if (!form) return;

    if (form.id === "form-buscar") {
        var campo = form.querySelector('input[name="q"]');
        var valor = (campo && campo.value ? campo.value : "").trim();
        e.preventDefault();
        rpBuscarDiscos(campo ? campo.value : valor, campo);
        return;
    }

    if (form.id === "form-filtrar-peliculas") {
        e.preventDefault();
        rpCargar(rpUrlFiltrosPeliculas(), true);
        return;
    }

    if (form.id === "form-buscar-global") {
        var gcampo = form.querySelector('input[name="q"]');
        var gvalor = (gcampo && gcampo.value ? gcampo.value : "").trim();
        e.preventDefault();
        rpCargar("/buscar/?q=" + encodeURIComponent(gvalor), true);
    }
});

rpEscuchar(document, "click", "discos:stock", function(e) {
    var btn = e.target && e.target.closest ? e.target.closest(".toggle-stock") : null;
    if (!btn) return;
    e.preventDefault();
    var id = btn.getAttribute("data-id");
    var nuevo = btn.classList.contains("badge-stock-no") ? 1 : 0;
    btn.disabled = true;
    btn.setAttribute("aria-busy", "true");
    var fd = new FormData();
    fd.append("en_stock", nuevo);
    fetch("/discos/" + id + "/stock", { method: "POST", body: fd, credentials: "same-origin", headers: { "X-CSRF-Token": rpCsrfToken() } })
        .then(function(r) {
            if (!r.ok) throw new Error();
            return r.json();
        })
        .then(function(d) {
            rpInvalidarCacheDiscos();
            var disponible = Number(d.en_stock) === 1;
            btn.classList.toggle("badge-stock-si", disponible);
            btn.classList.toggle("badge-stock-no", !disponible);
            btn.textContent = disponible ? "En stock" : "Sin stock";
            btn.setAttribute("aria-pressed", disponible ? "true" : "false");
            var nombre = btn.getAttribute("data-titulo") || "este disco";
            btn.setAttribute("aria-label", "Disponibilidad: " + nombre);
            btn.disabled = false;
            btn.setAttribute("aria-busy", "false");
        })
        .catch(function() {
            btn.disabled = false;
            btn.setAttribute("aria-busy", "false");
            rpToast("No se pudo cambiar el stock");
        });
});

rpEscuchar(document, "input", "discos:input", function(e) {
    var target = e.target;
    if (!target || target.id !== "buscar-discos") return;
    rpLiveSearch(target);
});

rpEscuchar(document, "change", "discos:change", function(e) {
    var target = e.target;
    if (!target) return;

    if (target.id === "filtro-genero-peliculas" || target.id === "filtro-decada-peliculas") {
        rpCargar(rpUrlFiltrosPeliculas(), true);
        return;
    }

    if (target.id === "filtro-genero-musica") {
        var murl = "/musica/";
        if (target.value) murl += "?genero=" + encodeURIComponent(target.value);
        rpCargar(murl, true);
        return;
    }

    if (target.id !== "filtro-stock" && target.id !== "filtro-genero" && target.id !== "filtro-decada") return;
    var campo = document.getElementById("buscar-discos");
    var valor = campo && campo.value ? campo.value : "";
    rpBuscarDiscos(valor, campo);
});

/* ============================================================
   PREFETCH por hover / touch
============================================================ */

rpEscuchar(document, "pointerover", "prefetch:over", function(e) {
    var a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a || !rpEsNavegable(a)) return;
    clearTimeout(rpPrefetchTimers.get(a));
    rpPrefetchTimers.set(a, setTimeout(function() {
        rpPrefetch(a.href);
    }, 150));
}, true);

rpEscuchar(document, "pointerdown", "prefetch:down", function(e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    var a = e.target && e.target.closest ? e.target.closest("a") : null;
    if (!a || !rpEsNavegable(a)) return;
    clearTimeout(rpPrefetchTimers.get(a));
    rpPrefetch(a.href);
}, true);

/* ============================================================
   ATAJOS DE TECLADO
============================================================ */

function rpEsControlInteractivo(target) {
    if (!target || !target.tagName) return false;
    var etiquetas = ["BUTTON", "A", "INPUT", "TEXTAREA", "SELECT", "OPTION", "SUMMARY", "AUDIO", "VIDEO", "DETAILS", "IFRAME", "OBJECT", "EMBED"];
    var roles = ["button", "link", "checkbox", "radio", "switch", "tab", "menuitem", "menuitemcheckbox", "menuitemradio", "option", "combobox", "listbox", "textbox", "searchbox", "slider", "spinbutton", "treeitem"];
    var elemento = target;
    while (elemento && elemento.nodeType === 1) {
        var tag = (elemento.tagName || "").toUpperCase();
        if (etiquetas.indexOf(tag) !== -1) return true;
        if (elemento.isContentEditable) return true;
        var editable = elemento.getAttribute && elemento.getAttribute("contenteditable");
        if (editable !== null && editable !== undefined && editable.toLowerCase() !== "false") return true;
        var role = elemento.getAttribute && elemento.getAttribute("role");
        if (role && roles.indexOf(role.toLowerCase()) !== -1) return true;
        var tabindex = elemento.getAttribute && elemento.getAttribute("tabindex");
        if (tabindex !== null && tabindex !== undefined && parseInt(tabindex, 10) >= 0) return true;
        elemento = elemento.parentElement;
    }
    return false;
}

rpEscuchar(document, "keydown", "shortcuts:keydown", function(e) {
    if (e.defaultPrevented || e.isComposing || e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
    if (rpEsControlInteractivo(e.target) || !rpAudio || !rpAudio.src) return;

    switch (e.key) {
        case " ":
        case "Space":
        case "Spacebar":
        case "k":
        case "K":
            e.preventDefault();
            rpToggle();
            break;
        case "ArrowUp":
            e.preventDefault();
            rpAudio.volume = Math.min(1, (rpAudio.volume || 0) + 0.05);
            if (rpVolumenSlider) rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
            rpGuardar();
            break;
        case "ArrowDown":
            e.preventDefault();
            rpAudio.volume = Math.max(0, (rpAudio.volume || 0) - 0.05);
            if (rpVolumenSlider) rpVolumenSlider.value = Math.round(rpAudio.volume * 100);
            rpGuardar();
            break;
        case "ArrowLeft":
            e.preventDefault();
            rpSaltar(-5);
            break;
        case "ArrowRight":
            e.preventDefault();
            rpSaltar(5);
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
    if (rpEstado.inicializado) {
        rpInitFormularios();
        rpBarraActualizar();
        rpActualizarActivos();
        return;
    }
    rpEstado.inicializado = true;
    rpRestore();
    rpInitFormularios();
    rpBarraActualizar();
    rpActualizarActivos();
    rpMedirReproductor();
    rpAutoOcultarFlash();
}

function rpSalir() {
    rpRevocarPreviews();
    rpGuardar();
}

if (document.readyState === "loading") {
    rpEscuchar(document, "DOMContentLoaded", "init:dom", rpInitApp);
} else {
    rpInitApp();
}
rpEscuchar(window, "load", "init:load", rpInitApp);
rpEscuchar(window, "beforeunload", "init:beforeunload", rpSalir);
rpEscuchar(window, "pagehide", "init:pagehide", rpSalir);