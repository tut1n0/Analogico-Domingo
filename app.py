import logging
import os
import secrets

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routes.inicio import router as inicio_router
from routes.buscar import router as buscar_router
from routes.discos import router as discos_router
from routes.programas import router as programas_router
from routes.musica import router as musica_router
from routes.peliculas import router as peliculas_router
from routes.auth import router as auth_router

from database import (
    iniciar_conexion_request,
    cerrar_conexion_request,
)
from models import asegurar_columnas
from utils.csrf import csrf_middleware
from utils.render import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        asegurar_columnas()
    except Exception as e:
        logger.warning("Error al verificar/agregar columnas: %s", e)
    yield


app = FastAPI(
    title="Analógico Domingo",
    version="1.0",
    lifespan=lifespan
)

logger = logging.getLogger("analogico_domingo")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("VERCEL"):
        raise RuntimeError(
            "SECRET_KEY no está definida en las variables de entorno de Vercel. "
            "Agrega SECRET_KEY en Vercel Dashboard → Settings → Environment Variables."
        )
    SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "SECRET_KEY no definida: se generó una clave aleatoria "
        "(las sesiones se reiniciarán en cada reinicio)."
    )

app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=csrf_middleware,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=60 * 60 * 24 * 365
)


@app.middleware("http")
async def conexion_por_request(request, call_next):
    holder = iniciar_conexion_request()

    try:
        response = await call_next(request)
    finally:
        cerrar_conexion_request(holder)

    return response


@app.middleware("http")
async def cache_control(request, call_next):
    response = await call_next(request)

    path = request.url.path
    content_type = response.headers.get("content-type", "")

    if "text/html" in content_type:
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    elif path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    elif path.startswith("/uploads/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    return response


# Archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
if os.path.isdir("uploads"):
    app.mount(
        "/uploads",
        StaticFiles(directory="uploads"),
        name="uploads"
    )

# Rutas
app.include_router(inicio_router)
app.include_router(buscar_router)
app.include_router(discos_router)
app.include_router(programas_router)
app.include_router(musica_router)
app.include_router(peliculas_router)
app.include_router(auth_router)


# =====================================================
# PAGINAS DE ERROR
# =====================================================

ERRORES = {
    400: ("Petición inválida", "No pudimos entender lo que pediste."),
    401: ("Necesitás iniciar sesión", "Esta sección es sólo para quienes están conectados."),
    403: ("No tenés permiso", "Tu sesión pudo haber expirado. Volvé a iniciar sesión."),
    404: ("No encontramos esa página", "Puede que el enlace haya cambiado o que ya no exista."),
    422: ("No pudimos procesar los datos", "Revisá los campos del formulario e intentá de nuevo."),
    500: ("Algo falló de nuestro lado", "Ya lo estamos mirando. Probá de nuevo en un momento."),
}

ERROR_POR_DEFECTO = ("Error inesperado", "Ocurrió un problema y no pudimos completar la operación.")


def _quiere_json(request):
    """Las llamadas de la SPA y los XHR esperan JSON, no HTML."""
    if request.headers.get("x-partial") == "1":
        return False

    accept = request.headers.get("accept", "")

    if "application/json" in accept:
        return "text/html" not in accept

    return request.headers.get("x-requested-with") == "fetch"


def _respuesta_error(request, codigo):
    titulo, detalle = ERRORES.get(codigo, ERROR_POR_DEFECTO)

    if _quiere_json(request):
        return JSONResponse(status_code=codigo, content={"error": titulo})

    try:
        return render(
            request,
            "error.html",
            {"codigo": codigo, "titulo": titulo, "detalle": detalle},
            status=codigo,
        )
    except Exception:
        logger.exception("No se pudo renderizar la pagina de error %s", codigo)
        return HTMLResponse(
            "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"UTF-8\">"
            f"<title>{codigo}</title></head><body>"
            f"<h1>{codigo}</h1><p>{titulo}</p>"
            "<p><a href=\"/\">Volver al inicio</a></p></body></html>",
            status_code=codigo,
        )


@app.exception_handler(StarletteHTTPException)
async def error_http(request, exc):
    return _respuesta_error(request, exc.status_code)


@app.exception_handler(RequestValidationError)
async def error_validacion(request, exc):
    return _respuesta_error(request, 422)


@app.exception_handler(Exception)
async def error_servidor(request, exc):
    logger.exception("Error no controlado: %s", exc)
    return _respuesta_error(request, 500)