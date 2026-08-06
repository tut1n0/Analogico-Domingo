def optimizar_imagen(url, ancho):
    if not url:
        return url

    if "res.cloudinary.com" in url:
        marker = "/image/upload/"
        if marker in url and f"w_{ancho}" not in url:
            base, resto = url.split(marker, 1)
            return f"{base}{marker}w_{ancho},q_auto,f_auto/{resto}"

    return url
