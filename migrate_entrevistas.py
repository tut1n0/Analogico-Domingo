import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)

try:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entrevistas (
                id_entrevista SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                fecha VARCHAR(10),
                archivo_url VARCHAR(255),
                tipo_archivo VARCHAR(10) DEFAULT 'audio'
            );
        """)
        conn.commit()
        print("Tabla 'entrevistas' creada correctamente.")
finally:
    conn.close()