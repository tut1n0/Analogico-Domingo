from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from utils.render import render

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
def inicio(request: Request):

    return render(
        request,
        "index.html",
        {}
    )