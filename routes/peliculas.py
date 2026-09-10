import math
import logging

from fastapi import Query, HTTPException
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse

from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file
from utils.mensajes import flash
from utils.normalizacion import normalizar_genero
from config import POR_PAGINA

from models import (
    obtener_peliculas_paginados,
    contar_peliculas,
    obtener_pelicula,
    agregar_pelicula,
    actualizar_pelicula,
    eliminar_pelicula,
    obtener_generos_peliculas,
)

router = APIRouter(
    prefix="/peliculas",
    tags=["Peliculas"]
)

logger = logging.getLogger("analogico_domingo.peliculas")


# ======================================================
# LISTAR PELICULAS
# ======================================================

@router.get("/")
def listar_peliculas(
    request: Request,
    page: int = Query(1, ge=1),
    genero: str = Query("", max_length=100)
):

    filtro_genero = genero.strip() if genero else None

    peliculas = obtener_peliculas_paginados(page, POR_PAGINA, filtro_genero)
    total = contar_peliculas(filtro_genero)
    total_paginas = max(math.ceil(total / POR_PAGINA), 1)

    return render(
        request,
        "peliculas.html",
        {
            "peliculas": peliculas,
            "pagina": page,
            "total_paginas": total_paginas,
            "total": total,
            "genero": filtro_genero,
            "generos": obtener_generos_peliculas()
        }
    )


# ======================================================
# FORMULARIO NUEVA PELICULA
# ======================================================

@router.get("/nuevo")
def nueva_pelicula(request: Request):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    return render(request, "agregar_pelicula.html")


# ======================================================
# GUARDAR PELICULA
# ======================================================

@router.post("/nuevo")
def guardar_pelicula(

    request: Request,

    titulo: str = Form(...),
    director: str = Form(...),
    genero: str = Form(None),
    url_pelicula: str = Form(""),
    url_subtitulos: str = Form(""),

    portada: UploadFile = File(None)

):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:
        portada_url = ""

        if portada and portada.filename:
            portada_url = upload_file(portada, "peliculas")

        datos = {
            "titulo": titulo,
            "director": director,
            "genero": normalizar_genero(genero),
            "portada": portada_url,
            "url_pelicula": url_pelicula,
            "url_subtitulos": url_subtitulos
        }

        agregar_pelicula(datos)
    except Exception as e:
        logger.exception("Error al guardar pelicula")
        flash(request, [f"No se pudo guardar la pelicula: {e}"])
        return RedirectResponse(
            url="/peliculas/nuevo",
            status_code=303
        )

    flash(request, ["Pelicula guardada."])

    return RedirectResponse(
        url="/peliculas/",
        status_code=303
    )


# ======================================================
# FORMULARIO EDITAR PELICULA
# ======================================================

@router.get("/editar/{id_pelicula}")
def editar_pelicula(request: Request, id_pelicula: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    pelicula = obtener_pelicula(id_pelicula)

    if not pelicula:
        flash(request, ["Película no encontrada."])
        return RedirectResponse(url="/peliculas/", status_code=303)

    return render(
        request,
        "editar_pelicula.html",
        {
            "pelicula": pelicula
        }
    )


# ======================================================
# ACTUALIZAR PELICULA
# ======================================================

@router.post("/editar/{id_pelicula}")
def actualizar(
    request: Request,
    id_pelicula: int,

    titulo: str = Form(...),
    director: str = Form(...),
    genero: str = Form(None),
    url_pelicula: str = Form(""),
    url_subtitulos: str = Form(""),

    portada: UploadFile = File(None)

):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    try:
        pelicula_actual = obtener_pelicula(id_pelicula)

        if not pelicula_actual:
            flash(request, ["Película no encontrada."])
            return RedirectResponse(url="/peliculas/", status_code=303)

        portada_url = pelicula_actual["portada"]

        if portada and portada.filename:
            if portada_url:
                delete_file(portada_url)
            portada_url = upload_file(portada, "peliculas")

        datos = {
            "titulo": titulo,
            "director": director,
            "genero": normalizar_genero(genero),
            "portada": portada_url,
            "url_pelicula": url_pelicula,
            "url_subtitulos": url_subtitulos
        }

        actualizar_pelicula(id_pelicula, datos)
    except Exception as e:
        logger.exception("Error al actualizar pelicula")
        flash(request, [f"No se pudo actualizar la pelicula: {e}"])
        return RedirectResponse(
            url=f"/peliculas/editar/{id_pelicula}",
            status_code=303
        )

    flash(request, ["Pelicula actualizada."])

    return RedirectResponse(
        url="/peliculas/",
        status_code=303
    )


# ======================================================
# ELIMINAR
# ======================================================

@router.post("/eliminar/{id_pelicula}")
def eliminar(request: Request, id_pelicula: int):

    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:
        pelicula = obtener_pelicula(id_pelicula)

        if pelicula and pelicula["portada"]:
            delete_file(pelicula["portada"])

        eliminar_pelicula(id_pelicula)

        flash(request, ["Pelicula eliminada."])
    except Exception as e:
        logger.exception("Error al eliminar pelicula")
        flash(request, [f"No se pudo eliminar la pelicula: {e}"])

    return RedirectResponse(
        url="/peliculas/",
        status_code=303
    )
