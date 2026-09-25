CATEGORIAS_FLASH = frozenset(("success", "error"))


def flash(request, mensajes, categoria="success"):
    if categoria not in CATEGORIAS_FLASH:
        raise ValueError("Categoría de flash no válida")

    if isinstance(mensajes, str):
        mensajes = [mensajes]

    request.session["flash"] = [
        {
            "mensaje": mensaje,
            "categoria": categoria,
        }
        for mensaje in mensajes
    ]
