import os
import time
import uuid
import logging
import cloudinary
import cloudinary.utils
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("analogico_domingo.storage")

DB_DRIVER = os.getenv("DB_DRIVER", "sqlite")

if DB_DRIVER == "postgresql":
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )

IMAGENES_EXT = {"jpg", "jpeg", "png", "webp", "gif", "avif", "bmp"}
AUDIO_EXT = {"mp3", "wav", "ogg", "oga", "m4a", "aac", "flac", "opus", "wma"}
VIDEO_EXT = {"mp4", "webm", "mov", "mkv", "avi", "m4v"}
MEDIA_EXT = AUDIO_EXT | VIDEO_EXT

LIMITE_IMAGENES = 20 * 1024 * 1024
LIMITE_MEDIA = 500 * 1024 * 1024


def _extensiones_permitidas(folder):
    if folder in ("portadas", "peliculas"):
        return IMAGENES_EXT
    if folder == "videos":
        return VIDEO_EXT | AUDIO_EXT
    if folder == "programas":
        return AUDIO_EXT
    if folder == "musica":
        return IMAGENES_EXT | AUDIO_EXT
    return IMAGENES_EXT | MEDIA_EXT


def _limite_tamano(folder):
    if folder in ("portadas", "peliculas"):
        return LIMITE_IMAGENES
    return LIMITE_MEDIA


def _ext_archivo(nombre):
    return nombre.lower().rsplit(".", 1)[-1] if "." in nombre else ""


def _validar_archivo(file, folder):
    ext = _ext_archivo(file.filename or "")

    if ext not in _extensiones_permitidas(folder):
        permitidas = ", ".join(sorted(_extensiones_permitidas(folder)))
        raise ValueError(
            f"Tipo de archivo no permitido (.{ext}). Usá: {permitidas}."
        )

    limite = _limite_tamano(folder)
    tamaño = getattr(file, "size", None)

    if tamaño is not None and tamaño > limite:
        raise ValueError("El archivo supera el tamaño máximo permitido.")


def upload_file(file, folder):
    _validar_archivo(file, folder)

    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"

    if DB_DRIVER == "sqlite":
        return _upload_local(file, folder, filename, limite=_limite_tamano(folder))

    return _upload_cloudinary(file, folder, filename)


def upload_file_local(file, folder):
    _validar_archivo(file, folder)

    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    return _upload_local(file, folder, filename, limite=_limite_tamano(folder))


def delete_file(reference):
    if not reference:
        return

    if reference.startswith("http"):
        _delete_cloudinary(reference)
        return

    _delete_local(reference)


def _upload_local(file, folder, filename, limite=None):
    ruta = os.path.join("uploads", folder, filename)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    total = 0

    with open(ruta, "wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break

            total += len(chunk)

            if limite is not None and total > limite:
                buffer.close()
                os.remove(ruta)
                raise ValueError("El archivo supera el tamaño máximo permitido.")

            buffer.write(chunk)

    return f"/uploads/{folder}/{filename}"


def _upload_cloudinary(file, folder, filename):
    import cloudinary.uploader

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            public_id=os.path.splitext(filename)[0],
            resource_type="auto"
        )
        return result["secure_url"]
    except Exception as e:
        logger.exception("Error al subir archivo a Cloudinary")
        raise


def _delete_local(path):
    if path.startswith("/uploads/"):
        full = path.lstrip("/")
        if os.path.exists(full):
            os.remove(full)


def _delete_cloudinary(url):
    import cloudinary.uploader
    import cloudinary.api

    parts = url.split("/")
    public_id = "/".join(parts[-2:]).rsplit(".", 1)[0]

    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass


def get_upload_signature(folder):
    try:
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")

        timestamp = int(time.time())
        params_to_sign = {
            "folder": folder,
            "timestamp": timestamp,
        }
        signature = cloudinary.utils.api_sign_request(
            params_to_sign, api_secret
        )

        return {
            "upload_url": f"https://api.cloudinary.com/v1_1/{cloud_name}/upload",
            "api_key": api_key,
            "timestamp": timestamp,
            "signature": signature,
            "folder": folder,
        }
    except Exception as e:
        print(f"[SIGNATURE ERROR] {e}")
        raise
