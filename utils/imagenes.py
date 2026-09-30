import re

MARCADOR_UPLOAD = "/image/upload/"

RE_TRANSFORM = re.compile(r"^[a-z]+_(?:\d+|[a-z]+)(?:,|$)")


def _es_cloudinary(url):
    return bool(url) and MARCADOR_UPLOAD in url


def _fusionar(nuestros, previos):
    """Une transforms dejando el primero de cada clave (el nuestro gana)."""
    vistos = set()
    salida = []

    for token in nuestros + previos:
        clave = token.split("_", 1)[0] + "_"

        if clave not in vistos:
            vistos.add(clave)
            salida.append(token)

    return ",".join(salida)


def _con_transform(url, cadena):
    """Inserta (o fusiona) un transform de Cloudinary justo despues de /upload/.

    El formato es /upload/<transforms>/<version>/<public_id>, asi que la
    version NO se puede absorber dentro del transform: debe quedar despues."""
    if not _es_cloudinary(url):
        return url

    base, resto = url.split(MARCADOR_UPLOAD, 1)
    primero, separador, cola = resto.partition("/")

    if RE_TRANSFORM.match(primero):
        fusionado = _fusionar(cadena.split(","), primero.split(","))
        sufijo = f"/{cola}" if separador else ""
        return f"{base}{MARCADOR_UPLOAD}{fusionado}{sufijo}"

    return f"{base}{MARCADOR_UPLOAD}{cadena}/{resto}"


def optimizar_imagen(url, ancho):
    return _con_transform(url, f"w_{ancho},q_auto,f_auto")


def srcset_imagen(url, anchos):
    """Devuelve un srcset. Para imagenes locales (sin Cloudinary) devuelve la URL sola."""
    if not url:
        return ""

    if not _es_cloudinary(url):
        return url

    return ", ".join(
        f"{_con_transform(url, f'w_{ancho},q_auto,f_auto')} {ancho}w"
        for ancho in anchos
    )


def imagen_social(url):
    return _con_transform(url, "w_1200,h_630,c_fill,q_auto,f_auto")
