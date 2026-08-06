from fastapi.templating import Jinja2Templates
from utils.imagenes import optimizar_imagen

templates = Jinja2Templates(directory="templates")


def render(request, template, context=None):

    if context is None:
        context = {}

    context["session"] = request.session
    context["img"] = optimizar_imagen

    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context
    )