from fastapi import Query
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse

from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file

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

    portada_url = ""

    if portada and portada.filename:
        portada_url = upload_file(portada, "portadas")

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

    return render(
        request,
        "ver_disco.html",
        {
            "disco": disco,
            "editar": editar
        }
    )