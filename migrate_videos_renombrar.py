"""
Script de migracion: Renombrar tabla 'entrevistas' -> 'videos'
y columna 'id_entrevista' -> 'id_video'.

Ejecutar solo si existe la tabla 'entrevistas' con datos.

Uso:
    python migrate_videos_renombrar.py
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER", "sqlite")

if DB_DRIVER == "sqlite":
    import sqlite3
    DB_PATH = os.getenv("DB_PATH", "database.db")
    conn = sqlite3.connect(DB_PATH)
else:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

try:
    with conn.cursor() as cur:

        if DB_DRIVER == "sqlite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entrevistas'")
        else:
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='entrevistas')")

        existe = cur.fetchone()

        if not existe or not existe[0]:
            print("La tabla 'entrevistas' no existe. Nada que migrar.")
        else:
            if DB_DRIVER == "sqlite":
                cur.execute("ALTER TABLE entrevistas RENAME TO videos")
                cur.execute("ALTER TABLE videos RENAME COLUMN id_entrevista TO id_video")
            else:
                cur.execute("ALTER TABLE entrevistas RENAME TO videos")
                cur.execute("ALTER TABLE videos RENAME COLUMN id_entrevista TO id_video")

            conn.commit()
            print("Migracion completada: tabla 'videos', columna 'id_video'.")

finally:
    conn.close()
