from fastapi import Request
from fastapi.responses import RedirectResponse


def verificar_login(request: Request):

    if "usuario" not in request.session:

        return RedirectResponse(
            "/login",
            status_code=303
        )

    return None