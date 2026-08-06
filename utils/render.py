from fastapi.templating import Jinja2Templates
from utils.imagenes import optimizar_imagen, imagen_social

templates = Jinja2Templates(directory="templates")


def render(request, template, context=None):

    if context is None:
        context = {}

    context["session"] = request.session
    context["img"] = optimizar_imagen
    context["img_social"] = imagen_social

    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context
    )