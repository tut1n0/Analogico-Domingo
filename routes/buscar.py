from fastapi import APIRouter, Depends, Request, Query

from utils.csrf import verificar_csrf
from utils.render import render
from models import buscar_global

router = APIRouter(
    prefix="/buscar",
    tags=["Busqueda"],
    dependencies=[Depends(verificar_csrf)]
)

LIMITE_BUSQUEDA_GLOBAL = 6


@router.get("")
@router.get("/")
def buscar(
    request: Request,
    q: str = Query("", max_length=200),
):
    texto = q.strip() if q else ""

    resultados = buscar_global(texto) if texto else {}

    return render(
        request,
        "buscar.html",
        {
            "q": texto,
            "resultados": resultados,
            "limite_resultados": LIMITE_BUSQUEDA_GLOBAL if texto else None,
        }
    )
