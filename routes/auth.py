from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from utils.render import render
from utils.mensajes import flash
from utils.passwords import verificar_password, hash_password
from models import obtener_usuario, actualizar_password

router = APIRouter(
    tags=["Autenticación"]
)

INTENTOS_MAX = 5
VENTANA_SEG = 15 * 60
_bloqueos = {}


def _clave_login(request, usuario):
    ip = request.client.host if request.client else "?"
    return f"{ip}:{usuario}"


def _verificar_bloqueo(request, usuario):
    import time as _time

    ahora = _time.time()
    for clave in list(_bloqueos):
        intentos, inicio, bloqueado_hasta = _bloqueos[clave]
        if ahora > inicio + VENTANA_SEG:
            del _bloqueos[clave]

    datos = _bloqueos.get(_clave_login(request, usuario))

    if datos and datos[2] is not None and ahora < datos[2]:
        return True

    return False


def _registrar_intento(request, usuario, ok):
    import time as _time

    clave = _clave_login(request, usuario)
    ahora = _time.time()
    datos = _bloqueos.get(clave)

    if ok:
        _bloqueos.pop(clave, None)
        return

    if datos and ahora < datos[1] + VENTANA_SEG:
        intentos, inicio, _ = datos
        intentos += 1
        if intentos >= INTENTOS_MAX:
            _bloqueos[clave] = (intentos, inicio, ahora + VENTANA_SEG)
        else:
            _bloqueos[clave] = (intentos, inicio, None)
    else:
        _bloqueos[clave] = (1, ahora, None)


# ======================================================
# FORMULARIO LOGIN
# ======================================================

@router.get("/login")
def login(request: Request):

    return render(request, "login.html")


# ======================================================
# VALIDAR LOGIN
# ======================================================

@router.post("/login")
def validar_login(

    request: Request,

    usuario: str = Form(...),
    password: str = Form(...)

):

    if _verificar_bloqueo(request, usuario):
        flash(
            request,
            "Demasiados intentos fallidos. Esperá unos minutos antes de volver a intentar.",
            categoria="error"
        )
        return render(request, "login.html")

    datos_usuario = obtener_usuario(usuario)

    if datos_usuario is None:
        _registrar_intento(request, usuario, False)
        flash(request, "Usuario o contraseña incorrectos.", categoria="error")
        return render(request, "login.html")

    ok, requiere_rehash = verificar_password(
        password, datos_usuario["password"]
    )

    if not ok:
        _registrar_intento(request, usuario, False)
        flash(request, "Usuario o contraseña incorrectos.", categoria="error")
        return render(request, "login.html")

    _registrar_intento(request, usuario, True)

    if requiere_rehash:
        actualizar_password(
            datos_usuario["id_usuario"],
            hash_password(password)
        )

    request.session["usuario"] = datos_usuario["usuario"]
    request.session["id_usuario"] = datos_usuario["id_usuario"]

    return RedirectResponse(
        url="/",
        status_code=303
    )


# ======================================================
# CERRAR SESIÓN
# ======================================================

@router.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=303
    )