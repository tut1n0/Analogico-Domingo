import argparse
import os
import shutil
import sqlite3
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def eliminar_sqlite(ruta):
    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"No existe la base SQLite: {ruta}")

    respaldo = f"{ruta}.backup-antes-eliminar-videos-{datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(ruta, respaldo)

    conexion = sqlite3.connect(ruta)
    try:
        with conexion:
            conexion.execute("DROP TABLE IF EXISTS videos")
            conexion.execute("DROP TABLE IF EXISTS entrevistas")
    finally:
        conexion.close()

    return respaldo


def eliminar_postgresql():
    import psycopg2

    conexion = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "analogico_domingo"),
    )

    try:
        with conexion:
            with conexion.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS videos")
                cursor.execute("DROP TABLE IF EXISTS entrevistas")
    finally:
        conexion.close()


def main():
    parser = argparse.ArgumentParser(
        description="Elimina definitivamente las tablas de Videos y Entrevistas."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma la eliminación definitiva.",
    )
    args = parser.parse_args()

    if not args.confirm:
        raise SystemExit("La eliminación requiere --confirm.")

    driver = os.getenv("DB_DRIVER", "sqlite").lower()

    if driver == "sqlite":
        ruta = os.getenv("DB_PATH", "analogico_domingo.db")
        respaldo = eliminar_sqlite(ruta)
        print(f"Tablas de Videos eliminadas. Respaldo: {respaldo}")
        return

    if driver == "postgresql":
        eliminar_postgresql()
        print("Tablas de Videos eliminadas.")
        return

    raise SystemExit(f"DB_DRIVER no soportado: {driver}")


if __name__ == "__main__":
    main()
