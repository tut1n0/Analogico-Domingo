import math

from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from utils.render import render
from utils.auth import verificar_login
from utils.storage import delete_file, get_upload_signature

from models import (
    obtener_musica,
    obtener_musica_paginados,
    contar_musica,
    obtener_musica_por_id,
    agregar_musica,
    actualizar_musica,
    eliminar_musica,
)

router = APIRouter(
    prefix="/musica",
    tags=["Musica"]
)

POR_PAGINA = 20


@router.get("/")
def listar_musica(request: Request, page: int = Query(1, ge=1)):
    musica = obtener_musica_paginados(page, POR_PAGINA)
    total = contar_musica()
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)
    return render(
        request,
        "musica.html",
        {
            "musica": musica,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total
        }
    )


@router.get("/upload-url")
def upload_url(request: Request, folder: str = "musica"):
    respuesta = verificar_login(request)
    if respuesta:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})
    params = get_upload_signature(folder)
    return JSONResponse(content=params)


@router.post("/upload-local")
async def upload_local(request: Request, file: UploadFile = File(...), folder: str = "musica"):
    respuesta = verificar_login(request)
    if respuesta:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})

    try:
        import os, uuid

        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        if cloud_name:
            from utils.storage import _upload_cloudinary
            filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            url = _upload_cloudinary(file, folder, filename)
        else:
            from utils.storage import upload_file_local
            url = upload_file_local(file, folder)

        return JSONResponse(content={"url": url})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/nuevo")
def nuevo(request: Request):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta
    return render(request, "agregar_musica.html", {})


@router.post("/nuevo")
def guardar(
    request: Request,
    titulo: str = Form(...),
    artista: str = Form(...),
    anio: str = Form(""),
    descripcion: str = Form(""),
    portada_url: str = Form(""),
    audio_url: str = Form(""),
):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    try:
        datos = {
            "titulo": titulo,
            "artista": artista,
            "anio": anio,
            "descripcion": descripcion,
            "portada": portada_url,
            "audio": audio_url,
        }

        agregar_musica(datos)

        return RedirectResponse(url="/musica/", status_code=303)

    except Exception as e:
        print(f"[ERROR GUARDAR MUSICA] {e}")
        return HTMLResponse(content=f"Error al guardar: {e}", status_code=500)


@router.get("/editar/{id_musica}")
def editar(request: Request, id_musica: int):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    item = obtener_musica_por_id(id_musica)
    return render(request, "editar_musica.html", {"musica": item})


@router.post("/editar/{id_musica}")
def actualizar(
    request: Request,
    id_musica: int,
    titulo: str = Form(...),
    artista: str = Form(...),
    anio: str = Form(""),
    descripcion: str = Form(""),
    portada_url: str = Form(""),
    audio_url: str = Form(""),
):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    try:
        item = obtener_musica_por_id(id_musica)

        nombre_portada = item["portada"]
        if portada_url:
            delete_file(nombre_portada)
            nombre_portada = portada_url

        nombre_audio = item["audio"]
        if audio_url:
            delete_file(nombre_audio)
            nombre_audio = audio_url

        datos = {
            "titulo": titulo,
            "artista": artista,
            "anio": anio,
            "descripcion": descripcion,
            "portada": nombre_portada,
            "audio": nombre_audio,
        }

        actualizar_musica(id_musica, datos)

        return RedirectResponse(url="/musica/", status_code=303)

    except Exception as e:
        print(f"[ERROR ACTUALIZAR MUSICA] {e}")
        return HTMLResponse(content=f"Error al actualizar: {e}", status_code=500)


@router.get("/eliminar/{id_musica}")
def eliminar(request: Request, id_musica: int):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    item = obtener_musica_por_id(id_musica)

    if item["portada"]:
        delete_file(item["portada"])
    if item["audio"]:
        delete_file(item["audio"])

    eliminar_musica(id_musica)

    return RedirectResponse(url="/musica/", status_code=303)


@router.get("/{id_musica}")
def ver(request: Request, id_musica: int):
    item = obtener_musica_por_id(id_musica)
    return render(request, "ver_musica.html", {"musica": item})
