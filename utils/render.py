import os
import re

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.imagenes import optimizar_imagen, imagen_social
from utils.csrf import obtener_token

templates = Jinja2Templates(directory="templates")

_PATRON_MAIN = re.compile(r"<main[^>]*>(.*?)</main>", re.DOTALL | re.IGNORECASE)
_PATRON_HEAD = re.compile(r"<head[^>]*>(.*?)</head>", re.DOTALL | re.IGNORECASE)
_PATRON_TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)


def video_thumbnail(url):
    if not url or "cloudinary.com" not in url:
        return None
    marker = "/upload/"
    idx = url.find(marker)
    if idx == -1:
        return None
    base = url[:idx + len(marker)]
    rest = url[idx + len(marker):]
    root, _ = os.path.splitext(rest)
    return f"{base}w_120,h_90,c_fill,so_0/{root}.jpg"


def render(request, template, context=None):

    if context is None:
        context = {}

    context["request"] = request
    context["session"] = request.session
    context["img"] = optimizar_imagen
    context["img_social"] = imagen_social
    context["video_thumb"] = video_thumbnail
    context["csrf_token"] = obtener_token(request)
    context["flash"] = request.session.pop("flash", None)

    html = templates.env.get_template(template).render(context)

    if request.headers.get("x-partial") == "1":
        m = _PATRON_MAIN.search(html)
        if m:
            head = ""
            mh = _PATRON_HEAD.search(html)
            if mh:
                head = mh.group(1)
            if not head:
                titulo = ""
                mt = _PATRON_TITLE.search(html)
                if mt:
                    titulo = mt.group(1)
                head = "<title>" + titulo + "</title>"
            inner = m.group(1)
            html = (
                "<html><head>" + head +
                "</head><body><main>" + inner + "</main></body></html>"
            )

    return HTMLResponse(content=html)