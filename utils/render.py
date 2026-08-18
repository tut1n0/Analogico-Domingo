from fastapi.templating import Jinja2Templates
from utils.imagenes import optimizar_imagen, imagen_social

templates = Jinja2Templates(directory="templates")


def video_thumbnail(url):
    if not url or "cloudinary.com" not in url:
        return None
    marker = "/upload/"
    idx = url.find(marker)
    if idx == -1:
        return None
    base = url[:idx + len(marker)]
    rest = url[idx + len(marker):]
    return f"{base}w_120,h_90,c_fill,so_0/{rest}.jpg"


def render(request, template, context=None):

    if context is None:
        context = {}

    context["session"] = request.session
    context["img"] = optimizar_imagen
    context["img_social"] = imagen_social
    context["video_thumb"] = video_thumbnail

    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context
    )