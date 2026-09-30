import hmac
import secrets

from fastapi import HTTPException
from starlette.requests import Request

METODOS_SEGUROS = ("GET", "HEAD", "OPTIONS", "TRACE")


def obtener_token(request: Request) -> str:
    token = request.session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token

    return token


def validar_token(session_token, enviado) -> bool:
    if not session_token or not enviado:
        return False

    return hmac.compare_digest(session_token, enviado)


async def csrf_middleware(request: Request, call_next):
    """Solo garantiza que la sesion tenga token. La validacion vive en
    la dependencia `verificar_csrf`, porque leer el body en el middleware
    lo agotaria antes de que llegue a la ruta."""
    obtener_token(request)
    return await call_next(request)


async def token_valido(request: Request):
    """Acepta el token por header (XHR), query string o campo de formulario."""
    session_token = request.session.get("csrf_token")

    if validar_token(session_token, request.headers.get("x-csrf-token")):
        return True

    if validar_token(session_token, request.query_params.get("csrf_token")):
        return True

    if request.method in METODOS_SEGUROS:
        return False

    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return validar_token(session_token, form.get("csrf_token"))

    return False


async def verificar_csrf(request: Request):
    """Dependencia de router: valida el token en los metodos que modifican datos."""
    if request.method in METODOS_SEGUROS:
        return

    if not await token_valido(request):
        raise HTTPException(status_code=403, detail="Token CSRF inválido.")
