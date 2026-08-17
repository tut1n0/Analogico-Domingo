import math

from fastapi import APIRouter, Request, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file, get_upload_signature

from models import (
    obtener_entrevistas_paginados,
    contar_entrevistas,
    obtener_entrevista,
    agregar_entrevista,
    actualizar_entrevista,
    eliminar_entrevista,
)

router = APIRouter(
    prefix="/entrevistas",
    tags=["Entrevistas"]
)

POR_PAGINA = 20


# =====================================================
# LISTAR ENTREVISTAS
# =====================================================

@router.get("/")
def listar_entrevistas(request: Request, page: int = Query(1, ge=1)):

    entrevistas = obtener_entrevistas_paginados(page, POR_PAGINA)
    total = contar_entrevistas()
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "entrevistas.html",
        {
            "entrevistas": entrevistas,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total
        }
    )


# =====================================================
# UPLOAD SIGNATURE
# =====================================================

@router.get("/upload-url")
def upload_url(request: Request, folder: str = "entrevistas"):

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
def nueva_entrevista(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    return render(request, "agregar_entrevista.html")


# =====================================================
# GUARDAR ENTREVISTA
# =====================================================

@router.post("/nuevo")
def guardar_entrevista(

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
            nombre_archivo = upload_file(archivo, "entrevistas")

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

        agregar_entrevista(datos)

        return RedirectResponse(
            url="/entrevistas/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR GUARDAR ENTREVISTA] {e}")
        return HTMLResponse(
            content=f"Error al guardar entrevista: {e}",
            status_code=500
        )


# =====================================================
# FORMULARIO EDITAR
# =====================================================

@router.get("/editar/{id_entrevista}")
def editar(request: Request, id_entrevista: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    entrevista = obtener_entrevista(id_entrevista)

    return render(
        request,
        "editar_entrevista.html",
        {
            "entrevista": entrevista
        }
    )


# =====================================================
# ACTUALIZAR
# =====================================================

@router.post("/editar/{id_entrevista}")
def actualizar(

    request: Request,

    id_entrevista: int,

    titulo: str = Form(...),
    fecha: str = Form(""),
    archivo: UploadFile = File(None),
    archivo_url: str = Form(""),

):
    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        entrevista = obtener_entrevista(id_entrevista)

        nombre_archivo = entrevista["archivo_url"]

        if archivo_url:
            delete_file(nombre_archivo)
            nombre_archivo = archivo_url
        elif archivo and archivo.filename:
            delete_file(nombre_archivo)
            nombre_archivo = upload_file(archivo, "entrevistas")

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

        actualizar_entrevista(id_entrevista, datos)

        return RedirectResponse(
            url="/entrevistas/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR ACTUALIZAR ENTREVISTA] {e}")
        return HTMLResponse(
            content=f"Error al actualizar entrevista: {e}",
            status_code=500
        )


# =====================================================
# ELIMINAR
# =====================================================

@router.get("/eliminar/{id_entrevista}")
def eliminar(request: Request, id_entrevista: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    entrevista = obtener_entrevista(id_entrevista)

    if entrevista["archivo_url"]:
        delete_file(entrevista["archivo_url"])

    eliminar_entrevista(id_entrevista)

    return RedirectResponse(
        url="/entrevistas/",
        status_code=303
    )


# =====================================================
# VER DETALLE
# =====================================================

@router.get("/{id_entrevista}")
def ver_entrevista(request: Request, id_entrevista: int):

    entrevista = obtener_entrevista(id_entrevista)

    return render(
        request,
        "ver_entrevista.html",
        {
            "entrevista": entrevista
        }
    )
