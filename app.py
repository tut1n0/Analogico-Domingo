from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.inicio import router as inicio_router
from routes.discos import router as discos_router
from routes.programas import router as programas_router

app = FastAPI(
    title="Analógico Domingo",
    version="1.0"
)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

# Rutas
app.include_router(inicio_router)
app.include_router(discos_router)
app.include_router(programas_router)