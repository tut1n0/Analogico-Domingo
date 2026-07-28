import os
import uuid
import time
import shutil
import cloudinary
import cloudinary.utils
from dotenv import load_dotenv

load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER", "sqlite")

if DB_DRIVER == "postgresql":
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )


def upload_file(file, folder):
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"

    if DB_DRIVER == "sqlite":
        return _upload_local(file, folder, filename)

    return _upload_cloudinary(file, folder, filename)


def upload_file_local(file, folder):
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    return _upload_local(file, folder, filename)


def delete_file(reference):
    if not reference:
        return

    if reference.startswith("http"):
        _delete_cloudinary(reference)
        return

    _delete_local(reference)


def _upload_local(file, folder, filename):
    ruta = os.path.join("uploads", folder, filename)

    with open(ruta, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

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
        print(f"[CLOUDINARY UPLOAD ERROR] {e}")
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
