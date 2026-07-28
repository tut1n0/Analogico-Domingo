from typing import List

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from utils.render import render
from utils.auth import verificar_login
from utils.storage import upload_file, delete_file, get_upload_signature

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
# UPLOAD SIGNATURE (para subir archivos grandes directo a Cloudinary)
# =====================================================

@router.get("/upload-url")
def upload_url(request: Request, folder: str = "programas", resource_type: str = "video"):

    respuesta = verificar_login(request)

    if respuesta:
        return JSONResponse(
            status_code=401,
            content={"error": "No autenticado"}
        )

    params = get_upload_signature(folder, resource_type)

    return JSONResponse(content=params)


# =====================================================
# UPLOAD LOCAL (server-side upload a Cloudinary)
# =====================================================

@router.post("/upload-local")
async def upload_local(request: Request, file: UploadFile = File(...), folder: str = "programas"):
    respuesta = verificar_login(request)
    if respuesta:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})

    try:
        url = upload_file(file, folder)
        return JSONResponse(content={"url": url})
    except Exception as e:
        print(f"[UPLOAD LOCAL ERROR] {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


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

        return RedirectResponse(
            url="/programas/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR GUARDAR PROGRAMA] {e}")
        return HTMLResponse(
            content=f"Error al guardar programa: {e}",
            status_code=500
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
    audio_url: str = Form(""),
    discos: List[int] = Form([])

):
    respuesta = verificar_login(request)

    if respuesta:
        return respuesta

    try:

        programa = obtener_programa(id_programa)

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

        return RedirectResponse(
            url="/programas/",
            status_code=303
        )

    except Exception as e:
        print(f"[ERROR ACTUALIZAR PROGRAMA] {e}")
        return HTMLResponse(
            content=f"Error al actualizar programa: {e}",
            status_code=500
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
        delete_file(programa["audio"])

    eliminar_programa(id_programa)

    return RedirectResponse(
        url="/programas/",
        status_code=303
    )