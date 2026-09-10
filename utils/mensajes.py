def flash(request, mensajes):
    if isinstance(mensajes, str):
        mensajes = [mensajes]

    request.session["flash"] = list(mensajes)