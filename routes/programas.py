from typing import List
import math
import logging

from fastapi import APIRouter, Request, Form, UploadFile, File, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from utils.render import render
from utils.auth import verificar_login
from utils.mensajes import flash
from utils.storage import upload_file, delete_file, get_upload_signature
from config import POR_PAGINA

from models import (
    obtener_programas_paginados,
    contar_programas,
    obtener_programa,
    agregar_programa,
    actualizar_programa,
    eliminar_programa,
    obtener_discos,
    obtener_discos_pendientes,
    obtener_discos_programa,
    agregar_disco_a_programa,
    eliminar_discos_programa,
    marcar_disco_escuchado
)

router = APIRouter(
    prefix="/programas",
    tags=["Programas"]
)

logger = logging.getLogger("analogico_domingo.programas")




# =====================================================
# LISTAR PROGRAMAS
# =====================================================

@router.get("/")
def listar_programas(request: Request, page: int = Query(1, ge=1)):

    programas = obtener_programas_paginados(page, POR_PAGINA)
    total = contar_programas()
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "programas.html",
        {
            "programas": programas,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total
        }
    )


# =====================================================
# UPLOAD SIGNATURE (para subir archivos grandes directo a Cloudinary)
# =====================================================

@router.get("/upload-url")
def upload_url(request: Request, folder: str = "programas"):

    respuesta = verificar_login(request)

    if respuesta:
        return JSONResponse(
            status_code=401,
            content={"error": "No autenticado"}
        )

    params = get_upload_signature(folder)

    return JSONResponse(content=params)


# =====================================================
# FORMULARIO NUEVO
# =====================================================

@router.get("/nuevo")
def nuevo_programa(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    discos = obtener_discos_pendientes()

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
    audio_url: str = Form(""),
    discos: List[int] = Form([])

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        nombre_audio = audio_url

        if not nombre_audio and audio and audio.filename:
            nombre_audio = upload_file(audio, "programas")

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

        flash(request, ["Programa guardado."])

        return RedirectResponse(
            url="/programas/",
            status_code=303
        )

    except Exception as e:
        logger.exception("Error al guardar programa")
        flash(request, [f"No se pudo guardar el programa: {e}"])
        return RedirectResponse(
            url="/programas/nuevo",
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

    if not programa:
        flash(request, ["Programa no encontrado."])
        return RedirectResponse(url="/programas/", status_code=303)

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
# VER PROGRAMA
# =====================================================

@router.get("/{id_programa}")
def ver_programa(request: Request, id_programa: int):

    programa = obtener_programa(id_programa)

    if not programa:
        flash(request, ["Programa no encontrado."])
        return RedirectResponse(url="/programas/", status_code=303)

    discos_programa = obtener_discos_programa(id_programa)

    return render(
        request,
        "ver_programa.html",
        {
            "programa": programa,
            "discos_programa": discos_programa,
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
    audio_url: str = Form(""),
    discos: List[int] = Form([])

):
    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        programa = obtener_programa(id_programa)

        if not programa:
            flash(request, ["Programa no encontrado."])
            return RedirectResponse(url="/programas/", status_code=303)

        nombre_audio = programa["audio"]

        if audio_url:
            delete_file(nombre_audio)
            nombre_audio = audio_url
        elif audio and audio.filename:
            delete_file(nombre_audio)
            nombre_audio = upload_file(audio, "programas")

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

        flash(request, ["Programa actualizado."])

        return RedirectResponse(
            url="/programas/",
            status_code=303
        )

    except Exception as e:
        logger.exception("Error al actualizar programa")
        flash(request, [f"No se pudo actualizar el programa: {e}"])
        return RedirectResponse(
            url=f"/programas/editar/{id_programa}",
            status_code=303
        )


# =====================================================
# ELIMINAR
# =====================================================

@router.post("/eliminar/{id_programa}")
def eliminar(request: Request, id_programa: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:
        programa = obtener_programa(id_programa)

        if not programa:
            flash(request, ["Programa no encontrado."])
            return RedirectResponse(url="/programas/", status_code=303)

        if programa["audio"]:
            delete_file(programa["audio"])

        eliminar_programa(id_programa)

        flash(request, ["Programa eliminado."])
    except Exception as e:
        logger.exception("Error al eliminar programa")
        flash(request, [f"No se pudo eliminar el programa: {e}"])

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )