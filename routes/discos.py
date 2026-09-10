import math
import logging

from fastapi import Query, HTTPException
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse

from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file
from utils.mensajes import flash
from utils.normalizacion import normalizar_genero
from config import POR_PAGINA

from models import (
    obtener_discos,
    obtener_discos_paginados,
    contar_discos,
    obtener_disco,
    agregar_disco,
    actualizar_disco,
    actualizar_estado_stock,
    eliminar_disco,
    obtener_musica,
    obtener_generos_discos,
)

router = APIRouter(
    prefix="/discos",
    tags=["Discos"]
)

logger = logging.getLogger("analogico_domingo.discos")



# ======================================================
# LISTAR DISCOS
# ======================================================

@router.get("/")
def listar_discos(
    request: Request,
    page: int = Query(1, ge=1),
    q: str = Query("", max_length=200),
    stock: str = Query("", max_length=10),
    genero: str = Query("", max_length=100)
):

    texto = q.strip() if q else ""

    if stock in ("1", "0"):
        filtro_stock = int(stock)
    else:
        filtro_stock = None

    filtro_genero = genero.strip() if genero else None

    discos = obtener_discos_paginados(page, POR_PAGINA, texto, filtro_stock, filtro_genero)
    total = contar_discos(texto, filtro_stock, filtro_genero)
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "discos.html",
        {
            "discos": discos,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total,
            "q": texto,
            "stock": filtro_stock,
            "genero": filtro_genero,
            "generos": obtener_generos_discos()
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

    id_musica: str = Form(""),
    en_stock: str = Form("0"),

    portada: UploadFile = File(None)

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:
        portada_url = ""

        if portada and portada.filename:
            portada_url = upload_file(portada, "portadas")

        id_musica = int(id_musica) if id_musica else None

        datos = {

            "titulo": titulo,
            "artista": artista,
            "anio": anio,
            "genero": normalizar_genero(genero),
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
    except Exception as e:
        logger.exception("Error al guardar disco")
        flash(request, [f"No se pudo guardar el disco: {e}"])
        return RedirectResponse(
            url="/discos/nuevo",
            status_code=303
        )

    flash(request, ["Disco guardado."])

    return RedirectResponse(
        url="/discos/",
        status_code=303
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
    id_musica: str = Form(""),
    escuchado: str = Form(""),
    en_stock: str = Form("0"),

    portada: UploadFile = File(None)

):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    try:
        disco_actual = obtener_disco(id_disco)

        if not disco_actual:
            flash(request, ["Disco no encontrado."])
            return RedirectResponse(url="/discos/", status_code=303)

        portada_url = disco_actual["portada"]

        if portada and portada.filename:
            if portada_url:
                delete_file(portada_url)
            portada_url = upload_file(portada, "portadas")

        id_musica = int(id_musica) if id_musica else None

        datos = {

            "titulo": titulo,
            "artista": artista,
            "anio": anio,
            "genero": normalizar_genero(genero),
            "sello": sello,
            "productor": productor,
            "duracion": duracion,
            "descripcion": descripcion,
            "portada": portada_url,
            "id_musica": id_musica,
            "escuchado": 1 if escuchado in ("1", "on", "true") else 0,
            "en_stock": 1 if en_stock in ("1", "on", "true") else 0

        }

        actualizar_disco(id_disco, datos)
    except Exception as e:
        logger.exception("Error al actualizar disco")
        flash(request, [f"No se pudo actualizar el disco: {e}"])
        return RedirectResponse(
            url=f"/discos/{id_disco}?editar=1",
            status_code=303
        )

    flash(request, ["Disco actualizado."])

    return RedirectResponse(
        url=f"/discos/{id_disco}",
        status_code=303
    )


# ======================================================
# ELIMINAR
# ======================================================

@router.post("/eliminar/{id_disco}")
def eliminar(request: Request, id_disco: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:
        disco = obtener_disco(id_disco)

        if disco and disco["portada"]:
            delete_file(disco["portada"])

        eliminar_disco(id_disco)

        flash(request, ["Disco eliminado."])
    except Exception as e:
        logger.exception("Error al eliminar disco")
        flash(request, [f"No se pudo eliminar el disco: {e}"])

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

    if not disco:
        flash(request, ["Disco no encontrado."])
        return RedirectResponse(url="/discos/", status_code=303)

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


# ======================================================
# CAMBIAR STOCK (toggle rapido desde tarjeta)
# ======================================================

@router.post("/{id_disco}/stock")
def cambiar_stock(
    request: Request,
    id_disco: int,
    en_stock: str = Form("0")
):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    valor = 1 if en_stock in ("1", "on", "true") else 0

    actualizar_estado_stock(id_disco, valor)

    return JSONResponse({
        "ok": True,
        "en_stock": valor
    })