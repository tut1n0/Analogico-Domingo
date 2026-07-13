from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/", name="inicio")
def inicio(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )