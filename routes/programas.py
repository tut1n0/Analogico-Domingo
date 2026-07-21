import os
import shutil
import uuid

from typing import List

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from utils.render import render
from utils.auth import verificar_login

from models import (
    obtener_programas,
    obtener_programa,
    agregar_programa,
    actualizar_programa,
    eliminar_programa,
    obtener_discos,
    obtener_discos_programa,
    agregar_disco_a_programa,
    eliminar_discos_programa,
    marcar_disco_escuchado
)

router = APIRouter(
    prefix="/programas",
    tags=["Programas"]
)




# =====================================================
# LISTAR PROGRAMAS
# =====================================================

@router.get("/")
def listar_programas(request: Request):

    programas = obtener_programas()

    return render(
        request,
        "programas.html",
        {
            "programas": programas
        }
    )


# =====================================================
# FORMULARIO NUEVO
# =====================================================

@router.get("/nuevo")
def nuevo_programa(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    discos = obtener_discos()

    return render(
        request,
        "agregar_programa.html",
        {
            "discos": discos
        }
    )


# =====================================================
# GUARDAR PROGRAMA
# =====================================================

@router.post("/nuevo")
def guardar_programa(

    request: Request,

    numero: int = Form(...),
    fecha: str = Form(...),
    observaciones: str = Form(""),
    audio: UploadFile = File(None),
    discos: List[int] = Form([])

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    nombre_audio = ""

    if audio and audio.filename:

        extension = os.path.splitext(audio.filename)[1]
        nombre_audio = f"{uuid.uuid4()}{extension}"

        ruta = os.path.join(
            "uploads",
            "programas",
            nombre_audio
        )

        with open(ruta, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    datos = {

        "numero": numero,
        "fecha": fecha,
        "observaciones": observaciones,
        "audio": nombre_audio

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


# =====================================================
# FORMULARIO EDITAR
# =====================================================

@router.get("/editar/{id_programa}")
def editar(request: Request, id_programa: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    programa = obtener_programa(id_programa)

    discos = obtener_discos()

    discos_programa = obtener_discos_programa(id_programa)

    seleccionados = [
        d["id_disco"] for d in discos_programa
    ]

    return render(
        request,
        "editar_programa.html",
        {
            "programa": programa,
            "discos": discos,
            "seleccionados": seleccionados
        }
    )


# =====================================================
# ACTUALIZAR
# =====================================================

@router.post("/editar/{id_programa}")
def actualizar(
    request: Request,

    id_programa: int,

    numero: int = Form(...),
    fecha: str = Form(...),
    observaciones: str = Form(""),
    audio: UploadFile = File(None),
    discos: List[int] = Form([])

):
    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    programa = obtener_programa(id_programa)

    nombre_audio = programa["audio"]

    if audio and audio.filename:

        if nombre_audio:

            ruta_vieja = os.path.join(
                "uploads",
                "programas",
                nombre_audio
            )

            if os.path.exists(ruta_vieja):
                os.remove(ruta_vieja)

        extension = os.path.splitext(audio.filename)[1]

        nombre_audio = f"{uuid.uuid4()}{extension}"

        ruta = os.path.join(
            "uploads",
            "programas",
            nombre_audio
        )

        with open(ruta, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

    datos = {

        "numero": numero,
        "fecha": fecha,
        "observaciones": observaciones,
        "audio": nombre_audio

    }

    actualizar_programa(
        id_programa,
        datos
    )

    eliminar_discos_programa(id_programa)

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


# =====================================================
# ELIMINAR
# =====================================================

@router.get("/eliminar/{id_programa}")
def eliminar(request: Request, id_programa: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    programa = obtener_programa(id_programa)

    if programa["audio"]:

        ruta = os.path.join(
            "uploads",
            "programas",
            programa["audio"]
        )

        if os.path.exists(ruta):
            os.remove(ruta)

    eliminar_programa(id_programa)

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )