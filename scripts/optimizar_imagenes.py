"""Genera las imágenes optimizadas del sitio a partir de los originales.

Uso:
    python scripts/optimizar_imagenes.py

Genera:
    static/header-opt.jpg  -> header redimensionado + comprimido
    static/header-opt.webp -> variante WebP del header
    static/caratula.jpg    -> portada de respaldo (placeholder)
"""
import os

from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC = os.path.join(RAIZ, "static")
FUENTES = os.path.join(RAIZ, "assets-src")


def _redimensionar(img, ancho_max):
    if img.width > ancho_max:
        alto = int(img.height * ancho_max / img.width)
        img = img.resize((ancho_max, alto), Image.LANCZOS)
    return img


def _peso(ruta):
    return round(os.path.getsize(ruta) / 1024)


def optimizar_header():
    origen = os.path.join(FUENTES, "header.jpg")
    if not os.path.exists(origen):
        raise SystemExit(f"No existe {origen}. Mové el header original a assets-src/")

    img = Image.open(origen).convert("RGB")
    img = _redimensionar(img, 1920)

    destino_jpg = os.path.join(STATIC, "header-opt.jpg")
    img.save(destino_jpg, "JPEG", quality=78, optimize=True, progressive=True)
    print(f"OK: {destino_jpg} -> {_peso(destino_jpg)} KB")

    destino_webp = os.path.join(STATIC, "header-opt.webp")
    img.save(destino_webp, "WEBP", quality=80, method=6)
    print(f"OK: {destino_webp} -> {_peso(destino_webp)} KB")


def crear_caratula():
    img = Image.new("RGB", (400, 300), (60, 58, 50))
    destino = os.path.join(STATIC, "caratula.jpg")
    img.save(destino, "JPEG", quality=80, optimize=True)
    print(f"OK: {destino} -> {_peso(destino)} KB")


if __name__ == "__main__":
    optimizar_header()
    crear_caratula()