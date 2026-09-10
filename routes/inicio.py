from fastapi import APIRouter, Request
from utils.render import render

router = APIRouter()


@router.get("/")
def inicio(request: Request):

    return render(
        request,
        "index.html",
        {}
    )