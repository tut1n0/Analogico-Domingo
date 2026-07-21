from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.inicio import router as inicio_router
from routes.discos import router as discos_router
from routes.programas import router as programas_router
from starlette.middleware.sessions import SessionMiddleware
from routes.auth import router as auth_router


app = FastAPI(
    title="Analógico Domingo",
    version="1.0"
)

app.add_middleware(
    SessionMiddleware,
    secret_key="analogico_domingo"
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
app.include_router(auth_router)