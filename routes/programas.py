from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Form
from typing import List


from models import (
    obtener_programas,
    obtener_programa,
    agregar_programa,
    actualizar_programa,
    eliminar_programa,
    obtener_discos_pendientes,
    agregar_disco_a_programa,
    marcar_disco_escuchado
)

router = APIRouter(
    prefix="/programas",
    tags=["Programas"]
)

templates = Jinja2Templates(directory="templates")


# ======================================================
# LISTAR PROGRAMAS
# ======================================================

@router.get("/")
def listar_programas(request: Request):

    programas = obtener_programas()

    return templates.TemplateResponse(
        request=request,
        name="programas.html",
        context={
            "programas": programas
        }
    )


# ======================================================
# FORMULARIO NUEVO
# ======================================================

@router.get("/nuevo")
def nuevo_programa(request: Request):

    discos = obtener_discos_pendientes()

    return templates.TemplateResponse(
        request=request,
        name="agregar_programa.html",
        context={
            "discos": discos
        }
    )

# ======================================================
# GUARDAR
# ======================================================

@router.post("/nuevo")
def guardar_programa(

    numero: int = Form(...),
    fecha: str = Form(...),
    observaciones: str = Form(""),

    discos: List[int] = Form([])

):

    datos = {

        "numero": numero,
        "fecha": fecha,
        "observaciones": observaciones

    }

    id_programa = agregar_programa(datos)

    for id_disco in discos:

        agregar_disco_a_programa(
            id_programa,
            id_disco
        )

        marcar_disco_escuchado(id_disco)

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )


# ======================================================
# FORMULARIO EDITAR
# ======================================================

@router.get("/editar/{id_programa}")
def editar_programa(request: Request, id_programa: int):

    programa = obtener_programa(id_programa)

    return templates.TemplateResponse(
        request=request,
        name="editar_programa.html",
        context={
            "programa": programa
        }
    )


# ======================================================
# ACTUALIZAR
# ======================================================

@router.post("/editar/{id_programa}")
def actualizar(

    id_programa: int,

    numero: int = Form(...),
    fecha: str = Form(...),
    observaciones: str = Form(None)

):

    datos = {

        "numero": numero,
        "fecha": fecha,
        "observaciones": observaciones

    }

    actualizar_programa(id_programa, datos)

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )


# ======================================================
# ELIMINAR
# ======================================================

@router.get("/eliminar/{id_programa}")
def eliminar(id_programa: int):

    eliminar_programa(id_programa)

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )