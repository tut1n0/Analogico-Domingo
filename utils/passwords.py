import hashlib
import hmac
import os

ITERACIONES = 600_000
ALGORITMO = "sha256"
PREFIJO = "pbkdf2"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        ALGORITMO,
        password.encode("utf-8"),
        salt,
        ITERACIONES,
    )
    return f"{PREFIJO}:{ALGORITMO}:{ITERACIONES}:{salt.hex()}:{digest.hex()}"


def _verificar_hash(password: str, almacenada: str) -> bool:
    try:
        _, algoritmo, iteraciones, salt_hex, digest_hex = almacenada.split(":")
        digest = hashlib.pbkdf2_hmac(
            algoritmo,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iteraciones),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def es_hash(password_almacenada: str) -> bool:
    return bool(password_almacenada) and password_almacenada.startswith(PREFIJO + ":")


def verificar_password(password: str, almacenada: str):
    """Devuelve (ok, requiere_rehash)."""

    if es_hash(almacenada):
        return _verificar_hash(password, almacenada), False

    # Compatibilidad con contraseñas legacy (texto plano)
    return hmac.compare_digest(password, almacenada), True