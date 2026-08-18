import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.inicio import router as inicio_router
from routes.discos import router as discos_router
from routes.programas import router as programas_router
from routes.musica import router as musica_router
from routes.videos import router as videos_router
from starlette.middleware.sessions import SessionMiddleware
from routes.auth import router as auth_router

from database import (
    iniciar_conexion_request,
    cerrar_conexion_request,
)


app = FastAPI(
    title="Analógico Domingo",
    version="1.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "analogico_domingo")
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

    if path.startswith("/static/"):
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
app.include_router(discos_router)
app.include_router(programas_router)
app.include_router(musica_router)
app.include_router(videos_router)
app.include_router(auth_router)