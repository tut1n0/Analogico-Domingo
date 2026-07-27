from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, upload_file_local, delete_file, get_upload_signature

from models import (
    obtener_musica,
    obtener_musica_por_id,
    agregar_musica,
    actualizar_musica,
    eliminar_musica,
)

router = APIRouter(
    prefix="/musica",
    tags=["Musica"]
)


@router.get("/")
def listar_musica(request: Request):
    musica = obtener_musica()
    return render(request, "musica.html", {"musica": musica})


@router.get("/upload-url")
def upload_url(request: Request, folder: str = "musica"):
    respuesta = verificar_login(request)
    if respuesta:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})
    params = get_upload_signature(folder)
    return JSONResponse(content=params)


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
    portada: UploadFile = File(None),
    portada_url: str = Form(""),
    audio: UploadFile = File(None),
    audio_url: str = Form(""),
):
    respuesta = verificar_login(request)
    if respuesta:
        return respuesta

    try:
        nombre_portada = portada_url
        if not nombre_portada and portada and portada.filename:
            nombre_portada = upload_file(portada, "musica")

        nombre_audio = audio_url
        if not nombre_audio and audio and audio.filename:
            nombre_audio = upload_file_local(audio, "musica")

        datos = {
            "titulo": titulo,
            "artista": artista,
            "anio": anio,
            "descripcion": descripcion,
            "portada": nombre_portada,
            "audio": nombre_audio,
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
    portada: UploadFile = File(None),
    portada_url: str = Form(""),
    audio: UploadFile = File(None),
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
        elif portada and portada.filename:
            delete_file(nombre_portada)
            nombre_portada = upload_file(portada, "musica")

        nombre_audio = item["audio"]
        if audio_url:
            delete_file(nombre_audio)
            nombre_audio = audio_url
        elif audio and audio.filename:
            delete_file(nombre_audio)
            nombre_audio = upload_file_local(audio, "musica")

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
