import contextvars
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_DRIVER = os.getenv("DB_DRIVER", "sqlite")

_conexion_request = contextvars.ContextVar("conexion_request", default=None)


class SqliteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self._cursor = sqlite_cursor

    def execute(self, sql, params=None):
        self._cursor.execute(sql, params or ())

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class SqliteConnectionWrapper:
    def __init__(self, sqlite_conn, compartida=False):
        self._conn = sqlite_conn
        self._compartida = compartida

    def cursor(self):
        return SqliteCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._compartida:
            return
        self._conn.close()


class PgCursorWrapper:
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self._lastrowid = None

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        self._cursor.execute(sql, params or ())
        if sql.strip().upper().startswith("INSERT"):
            try:
                self._cursor.execute("SELECT LASTVAL()")
                self._lastrowid = self._cursor.fetchone()["lastval"]
            except Exception:
                self._lastrowid = None

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._cursor.close()


class PgConnectionWrapper:
    def __init__(self, pg_conn, compartida=False):
        self._conn = pg_conn
        self._compartida = compartida

    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return PgCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._compartida:
            return
        self._conn.close()


def _nueva_conexion():
    if DB_DRIVER == "sqlite":
        conn = sqlite3.connect(
            "analogico_domingo.db",
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return SqliteConnectionWrapper(conn)

    elif DB_DRIVER == "postgresql":
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            database=os.getenv("DB_NAME", "analogico_domingo"),
        )
        return PgConnectionWrapper(conn)

    else:
        raise ValueError(f"DB_DRIVER desconocido: {DB_DRIVER}")


def get_connection():
    holder = _conexion_request.get()

    if holder is not None:
        if holder["conexion"] is None:
            conexion = _nueva_conexion()
            conexion._compartida = True
            holder["conexion"] = conexion
        return holder["conexion"]

    return _nueva_conexion()


def iniciar_conexion_request():
    holder = {"conexion": None}
    _conexion_request.set(holder)
    return holder


def cerrar_conexion_request(holder):
    conexion = holder["conexion"]

    if conexion is not None:
        try:
            conexion._compartida = False
            conexion.close()
        except Exception:
            pass

    _conexion_request.set(None)
