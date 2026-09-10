import hmac
import secrets

from starlette.requests import Request
from starlette.responses import JSONResponse

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
    if request.method in METODOS_SEGUROS:
        obtener_token(request)
        return await call_next(request)

    session_token = request.session.get("csrf_token")
    enviado = (
        request.headers.get("x-csrf-token")
        or request.query_params.get("csrf_token")
    )

    if not validar_token(session_token, enviado):
        return JSONResponse(
            status_code=403,
            content={"error": "Token CSRF inválido."}
        )

    return await call_next(request)