def normalizar_genero(texto):
    if not texto:
        return texto

    partes = [p.strip() for p in texto.split(",") if p.strip()]

    if not partes:
        return None

    normalizadas = []
    for parte in partes:
        palabras = parte.split()
        titulada = " ".join(
            palabra[:1].upper() + palabra[1:] for palabra in palabras
        )
        normalizadas.append(titulada)

    return ", ".join(normalizadas)