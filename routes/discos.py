import math

from fastapi import Query
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse

from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file
from config import POR_PAGINA

from models import (
    obtener_discos,
    obtener_discos_paginados,
    contar_discos,
    obtener_disco,
    agregar_disco,
    actualizar_disco,
    eliminar_disco,
    obtener_musica
)

router = APIRouter(
    prefix="/discos",
    tags=["Discos"]
)



# ======================================================
# LISTAR DISCOS
# ======================================================

@router.get("/")
def listar_discos(
    request: Request,
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=200)
):

    texto = q.strip() if q else ""

    discos = obtener_discos_paginados(page, POR_PAGINA, texto)
    total = contar_discos(texto)
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "discos.html",
        {
            "discos": discos,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total,
            "q": texto
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

    musica_list = obtener_musica()

    return render(
        request,
        "agregar_disco.html",
        {
            "musica_list": musica_list
        }
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

    id_musica_raw: str = Form(""),
    en_stock: str = Form("0"),

    portada: UploadFile = File(None)

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    portada_url = ""

    if portada and portada.filename:
        portada_url = upload_file(portada, "portadas")

    id_musica = int(id_musica_raw) if id_musica_raw else None

    datos = {

        "titulo": titulo,
        "artista": artista,
        "anio": anio,
        "genero": genero,
        "sello": sello,
        "productor": productor,
        "duracion": duracion,
        "descripcion": descripcion,
        "portada": portada_url,
        "id_musica": id_musica,
        "escuchado": 0,
        "en_stock": 1 if en_stock in ("1", "on", "true") else 0

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
    id_musica_raw: str = Form(""),
    escuchado: bool = Form(False),
    en_stock: str = Form("0"),

    portada: UploadFile = File(None)

):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    disco_actual = obtener_disco(id_disco)

    portada_url = disco_actual["portada"]

    if portada and portada.filename:
        if portada_url:
            delete_file(portada_url)
        portada_url = upload_file(portada, "portadas")

    id_musica = int(id_musica_raw) if id_musica_raw else None

    datos = {

        "titulo": titulo,
        "artista": artista,
        "anio": anio,
        "genero": genero,
        "sello": sello,
        "productor": productor,
        "duracion": duracion,
        "descripcion": descripcion,
        "portada": portada_url,
        "id_musica": id_musica,
        "escuchado": int(escuchado),
        "en_stock": 1 if en_stock in ("1", "on", "true") else 0

    }

    actualizar_disco(id_disco, datos)

    return RedirectResponse(
        url=f"/discos/{id_disco}",
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

    disco = obtener_disco(id_disco)

    if disco and disco["portada"]:
        delete_file(disco["portada"])

    eliminar_disco(id_disco)

    return RedirectResponse(
        url="/discos/",
        status_code=303
    )

# ======================================================
# VER DISCO
# ======================================================

@router.get("/{id_disco}")
def ver_disco(
    request: Request,
    id_disco: int,
    editar: bool = Query(False)
):

    disco = obtener_disco(id_disco)
    musica_list = obtener_musica()

    return render(
        request,
        "ver_disco.html",
        {
            "disco": disco,
            "editar": editar,
            "musica_list": musica_list
        }
    )