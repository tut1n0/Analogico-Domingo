import math

from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file, get_upload_signature
from config import POR_PAGINA

from models import (
    obtener_videos_paginados,
    contar_videos,
    obtener_video,
    agregar_video,
    actualizar_video,
    eliminar_video,
)

router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)


# =====================================================
# LISTAR VIDEOS
# =====================================================

@router.get("/")
def listar_videos(request: Request, page: int = Query(1, ge=1)):

    videos = obtener_videos_paginados(page, POR_PAGINA)
    total = contar_videos()
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "videos.html",
        {
            "videos": videos,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total
        }
    )


# =====================================================
# UPLOAD SIGNATURE
# =====================================================

@router.get("/upload-url")
def upload_url(request: Request, folder: str = "videos"):

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
def nuevo_video(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    return render(request, "agregar_video.html")


# =====================================================
# GUARDAR VIDEO
# =====================================================

@router.post("/nuevo")
def guardar_video(

    request: Request,

    titulo: str = Form(...),
    fecha: str = Form(""),
    archivo: UploadFile = File(None),
    archivo_url: str = Form(""),

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        nombre_archivo = archivo_url

        if not nombre_archivo and archivo and archivo.filename:
            nombre_archivo = upload_file(archivo, "videos")

        # Determinar tipo de archivo
        tipo = "audio"
        if nombre_archivo:
            ext = nombre_archivo.lower().rsplit(".", 1)[-1] if "." in nombre_archivo else ""
            if ext in ("mp4", "webm", "ogg", "mov", "avi", "mkv"):
                tipo = "video"

        datos = {
            "titulo": titulo,
            "fecha": fecha,
            "archivo_url": nombre_archivo,
            "tipo_archivo": tipo
        }

        agregar_video(datos)

        return RedirectResponse(
            url="/videos/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR GUARDAR VIDEO] {e}")
        return HTMLResponse(
            content=f"Error al guardar video: {e}",
            status_code=500
        )


# =====================================================
# FORMULARIO EDITAR
# =====================================================

@router.get("/editar/{id_video}")
def editar(request: Request, id_video: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    video = obtener_video(id_video)

    return render(
        request,
        "editar_video.html",
        {
            "video": video
        }
    )


# =====================================================
# ACTUALIZAR
# =====================================================

@router.post("/editar/{id_video}")
def actualizar(

    request: Request,

    id_video: int,

    titulo: str = Form(...),
    fecha: str = Form(""),
    archivo: UploadFile = File(None),
    archivo_url: str = Form(""),

):
    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        video = obtener_video(id_video)

        nombre_archivo = video["archivo_url"]

        if archivo_url:
            delete_file(nombre_archivo)
            nombre_archivo = archivo_url
        elif archivo and archivo.filename:
            delete_file(nombre_archivo)
            nombre_archivo = upload_file(archivo, "videos")

        tipo = "audio"
        if nombre_archivo:
            ext = nombre_archivo.lower().rsplit(".", 1)[-1] if "." in nombre_archivo else ""
            if ext in ("mp4", "webm", "ogg", "mov", "avi", "mkv"):
                tipo = "video"

        datos = {
            "titulo": titulo,
            "fecha": fecha,
            "archivo_url": nombre_archivo,
            "tipo_archivo": tipo
        }

        actualizar_video(id_video, datos)

        return RedirectResponse(
            url="/videos/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR ACTUALIZAR VIDEO] {e}")
        return HTMLResponse(
            content=f"Error al actualizar video: {e}",
            status_code=500
        )


# =====================================================
# ELIMINAR
# =====================================================

@router.get("/eliminar/{id_video}")
def eliminar(request: Request, id_video: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    video = obtener_video(id_video)

    if video["archivo_url"]:
        delete_file(video["archivo_url"])

    eliminar_video(id_video)

    return RedirectResponse(
        url="/videos/",
        status_code=303
    )


# =====================================================
# VER DETALLE
# =====================================================

@router.get("/{id_video}")
def ver_video(request: Request, id_video: int):

    video = obtener_video(id_video)

    return render(
        request,
        "ver_video.html",
        {
            "video": video
        }
    )
