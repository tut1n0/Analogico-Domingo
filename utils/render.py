import re

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.imagenes import optimizar_imagen, imagen_social
from utils.csrf import obtener_token

templates = Jinja2Templates(directory="templates")

_PATRON_MAIN = re.compile(r"<main[^>]*>(.*?)</main>", re.DOTALL | re.IGNORECASE)
_PATRON_HEAD = re.compile(r"<head[^>]*>(.*?)</head>", re.DOTALL | re.IGNORECASE)
_PATRON_TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)


def render(request, template, context=None):

    if context is None:
        context = {}

    context["request"] = request
    context["session"] = request.session
    context["img"] = optimizar_imagen
    context["img_social"] = imagen_social
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