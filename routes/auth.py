from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from utils.render import render
from models import obtener_usuario

router = APIRouter(
    tags=["Autenticación"]
)


# ======================================================
# FORMULARIO LOGIN
# ======================================================

@router.get("/login")
def login(request: Request):

    return render(
        request,
        "login.html",
        {
            "error": ""
        }
    )


# ======================================================
# VALIDAR LOGIN
# ======================================================

@router.post("/login")
def validar_login(

    request: Request,

    usuario: str = Form(...),
    password: str = Form(...)

):

    datos_usuario = obtener_usuario(usuario)

    if datos_usuario is None:

        return render(
            request,
            "login.html",
            {
                "error": "Usuario o contraseña incorrectos."
            }
        )

    if datos_usuario["password"] != password:

        return render(
            request,
            "login.html",
            {
                "error": "Usuario o contraseña incorrectos."
            }
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