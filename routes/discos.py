import os
import shutil
import uuid 
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
 


from models import (
    obtener_discos,
    obtener_disco,
    agregar_disco,
    actualizar_disco,
    eliminar_disco
)

router = APIRouter(
    prefix="/discos",
    tags=["Discos"]
)

templates = Jinja2Templates(directory="templates")


# ======================================================
# LISTAR DISCOS
# ======================================================

@router.get("/")
def listar_discos(request: Request):

    discos = obtener_discos()

    return templates.TemplateResponse(
        request=request,
        name="discos.html",
        context={
            "discos": discos
        }
    )


# ======================================================
# FORMULARIO NUEVO DISCO
# ======================================================

@router.get("/nuevo")
def nuevo_disco(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="agregar_disco.html",
        context={}
    )


# ======================================================
# GUARDAR DISCO
# ======================================================

@router.post("/nuevo")
def guardar_disco(

    titulo: str = Form(...),
    artista: str = Form(...),
    anio: int = Form(None),
    genero: str = Form(None),
    sello: str = Form(None),
    productor: str = Form(None),
    duracion: str = Form(None),
    descripcion: str = Form(None),

    portada: UploadFile = File(None)

):

    nombre_portada = ""

    if portada and portada.filename:

        extension = os.path.splitext(portada.filename)[1]

        nombre_portada = f"{uuid.uuid4()}{extension}"

        ruta = os.path.join(
            "uploads",
            "portadas",
            nombre_portada
        )

        with open(ruta, "wb") as buffer:
            shutil.copyfileobj(portada.file, buffer)

    datos = {

        "titulo": titulo,
        "artista": artista,
        "anio": anio,
        "genero": genero,
        "sello": sello,
        "productor": productor,
        "duracion": duracion,
        "descripcion": descripcion,
        "portada": nombre_portada,
        "escuchado": False

    }

    agregar_disco(datos)

    return RedirectResponse(
        url="/discos/",
        status_code=303
    )


# ======================================================
# FORMULARIO EDITAR
# ======================================================

@router.get("/editar/{id_disco}")
def editar_disco(request: Request, id_disco: int):

    disco = obtener_disco(id_disco)

    return templates.TemplateResponse(
        request=request,
        name="editar_disco.html",
        context={
            "disco": disco
        }
    )


# ======================================================
# ACTUALIZAR DISCO
# ======================================================

@router.post("/editar/{id_disco}")
def actualizar(

    id_disco: int,

    titulo: str = Form(...),
    artista: str = Form(...),
    anio: int = Form(None),
    genero: str = Form(None),
    sello: str = Form(None),
    productor: str = Form(None),
    duracion: str = Form(None),
    descripcion: str = Form(None),
    escuchado: bool = Form(False)

):

    datos = {

        "titulo": titulo,
        "artista": artista,
        "anio": anio,
        "genero": genero,
        "sello": sello,
        "productor": productor,
        "duracion": duracion,
        "descripcion": descripcion,
        "portada": "",
        "escuchado": escuchado

    }

    actualizar_disco(id_disco, datos)

    return RedirectResponse(
        url="/discos/",
        status_code=303
    )


# ======================================================
# ELIMINAR
# ======================================================

@router.get("/eliminar/{id_disco}")
def eliminar(id_disco: int):

    eliminar_disco(id_disco)

    return RedirectResponse(
        url="/discos/",
        status_code=303
    )