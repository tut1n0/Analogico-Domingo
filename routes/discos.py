import os
import shutil
import uuid

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse

from utils.render import render
from utils.auth import verificar_login

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



# ======================================================
# LISTAR DISCOS
# ======================================================

@router.get("/")
def listar_discos(request: Request):

    discos = obtener_discos()

    return render(
        request,
        "discos.html",
        {
            "discos": discos
        }
    )


# ======================================================
# FORMULARIO NUEVO DISCO
# ======================================================

@router.get("/nuevo")
def nuevo_disco(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    return render(
        request,
        "agregar_disco.html",
        {}
    )


# ======================================================
# GUARDAR DISCO
# ======================================================

@router.post("/nuevo")
def guardar_disco(

    request: Request,

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

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

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

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    disco = obtener_disco(id_disco)

    return render(
        request,
        "editar_disco.html",
        {
            "disco": disco
        }
    )


# ======================================================
# ACTUALIZAR DISCO
# ======================================================

@router.post("/editar/{id_disco}")
def actualizar(
    request: Request,
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
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    disco_actual = obtener_disco(id_disco)
    
    datos = {

        "titulo": titulo,
        "artista": artista,
        "anio": anio,
        "genero": genero,
        "sello": sello,
        "productor": productor,
        "duracion": duracion,
        "descripcion": descripcion,
        "portada": disco_actual["portada"],
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
def eliminar(request: Request, id_disco: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    eliminar_disco(id_disco)

    return RedirectResponse(
        url="/discos/",
        status_code=303
    )

# ======================================================
# VER DISCO
# ======================================================

@router.get("/{id_disco}")
def ver_disco(request: Request, id_disco: int):

    disco = obtener_disco(id_disco)

    return render(
        request,
        "ver_disco.html",
        {
            "disco": disco
        }
    )