from database import get_connection


# ==========================================
# DISCOS
# ==========================================

def obtener_discos():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT d.*, m.audio AS musica_audio
                FROM discos d
                LEFT JOIN musica m ON d.id_musica = m.id_musica
                ORDER BY d.artista ASC, d.titulo ASC
            """

            cursor.execute(sql)

            return cursor.fetchall()

    finally:
        conexion.close()


def obtener_disco(id_disco):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT d.*, m.audio AS musica_audio
                FROM discos d
                LEFT JOIN musica m ON d.id_musica = m.id_musica
                WHERE d.id_disco = ?
            """

            cursor.execute(sql, (id_disco,))

            return cursor.fetchone()

    finally:
        conexion.close()


def obtener_discos_paginados(page, por_pagina):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT
                    d.id_disco,
                    d.titulo,
                    d.artista,
                    d.anio,
                    d.genero,
                    d.sello,
                    d.portada,
                    d.escuchado,
                    d.id_musica,
                    m.audio AS musica_audio
                FROM discos d
                LEFT JOIN musica m ON d.id_musica = m.id_musica
                ORDER BY d.artista ASC, d.titulo ASC
                LIMIT ? OFFSET ?
            """

            offset = (page - 1) * por_pagina

            cursor.execute(sql, (por_pagina, offset))

            return cursor.fetchall()

    finally:
        conexion.close()


def contar_discos():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            cursor.execute("SELECT COUNT(*) AS total FROM discos")

            fila = cursor.fetchone()

            return fila["total"] if fila else 0

    finally:
        conexion.close()


def agregar_disco(datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                INSERT INTO discos
                (
                    titulo,
                    artista,
                    anio,
                    genero,
                    sello,
                    productor,
                    duracion,
                    descripcion,
                    portada,
                    id_musica,
                    escuchado
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """

            cursor.execute(sql, (

                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["genero"],
                datos["sello"],
                datos["productor"],
                datos["duracion"],
                datos["descripcion"],
                datos["portada"],
                datos["id_musica"],
                datos["escuchado"]

            ))

            conexion.commit()

            return cursor.lastrowid

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def actualizar_disco(id_disco, datos):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = """
                UPDATE discos
                SET
                    titulo=?,
                    artista=?,
                    anio=?,
                    genero=?,
                    sello=?,
                    productor=?,
                    duracion=?,
                    descripcion=?,
                    portada=?,
                    id_musica=?,
                    escuchado=?
                WHERE id_disco=?
            """

            cursor.execute(sql, (

                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["genero"],
                datos["sello"],
                datos["productor"],
                datos["duracion"],
                datos["descripcion"],
                datos["portada"],
                datos["id_musica"],
                datos["escuchado"],
                id_disco

            ))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def eliminar_disco(id_disco):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = """
                DELETE FROM discos
                WHERE id_disco=?
            """

            cursor.execute(sql, (id_disco,))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def buscar_discos(texto):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM discos
                WHERE titulo LIKE ?
                   OR artista LIKE ?
                   OR genero LIKE ?
                   OR sello LIKE ?
                   OR productor LIKE ?
                ORDER BY artista, titulo
            """

            busqueda = f"%{texto}%"

            cursor.execute(sql, (
                busqueda,
                busqueda,
                busqueda,
                busqueda,
                busqueda,
                
            ))

            return cursor.fetchall()

    finally:

        conexion.close()

# ==========================================
# PROGRAMAS
# ==========================================

def obtener_programas():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM programas
                ORDER BY fecha DESC
            """

            cursor.execute(sql)

            return cursor.fetchall()

    finally:

        conexion.close()


def obtener_programas_paginados(page, por_pagina):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT id_programa, numero, fecha, observaciones, audio
                FROM programas
                ORDER BY fecha DESC
                LIMIT ? OFFSET ?
            """

            offset = (page - 1) * por_pagina

            cursor.execute(sql, (por_pagina, offset))

            return cursor.fetchall()

    finally:

        conexion.close()


def contar_programas():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            cursor.execute("SELECT COUNT(*) AS total FROM programas")

            fila = cursor.fetchone()

            return fila["total"] if fila else 0

    finally:

        conexion.close()


def obtener_programa(id_programa):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM programas
                WHERE id_programa = ?
            """

            cursor.execute(sql, (id_programa,))

            return cursor.fetchone()

    finally:

        conexion.close()


def agregar_programa(datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                INSERT INTO programas
                (
                    numero,
                    fecha,
                    observaciones,
                    audio
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?
                )
            """

            cursor.execute(sql, (

                datos["numero"],
                datos["fecha"],
                datos["observaciones"],
                datos["audio"]

            ))

            conexion.commit()

            return cursor.lastrowid

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def actualizar_programa(id_programa, datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                UPDATE programas
                SET
                    numero=?,
                    fecha=?,
                    observaciones=?,
                    audio=?
                WHERE id_programa=?
            """

            cursor.execute(sql, (

                datos["numero"],
                datos["fecha"],
                datos["observaciones"],
                datos["audio"],
                id_programa

            ))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def eliminar_programa(id_programa):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                DELETE FROM programas
                WHERE id_programa=?
            """

            cursor.execute(sql, (id_programa,))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()

def obtener_discos_pendientes():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM discos
                WHERE escuchado = 0
                ORDER BY artista, titulo
            """

            cursor.execute(sql)

            return cursor.fetchall()

    finally:

        conexion.close()

def agregar_disco_a_programa(id_programa, id_disco):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                INSERT INTO programa_disco
                (
                    id_programa,
                    id_disco
                )
                VALUES
                (
                    ?,
                    ?
                )
            """

            cursor.execute(sql, (
                id_programa,
                id_disco
            ))

            conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def obtener_discos_programa(id_programa):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT id_disco
                FROM programa_disco
                WHERE id_programa=?
            """

            cursor.execute(sql, (id_programa,))

            return cursor.fetchall()

    finally:

        conexion.close()


def eliminar_discos_programa(id_programa):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                DELETE FROM programa_disco
                WHERE id_programa=?
            """

            cursor.execute(sql, (id_programa,))

            conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()

def marcar_disco_escuchado(id_disco):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                UPDATE discos
                SET escuchado = 1
                WHERE id_disco = ?
            """

            cursor.execute(sql, (id_disco,))

            conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()
# ==========================================
# MUSICA
# ==========================================

def obtener_musica():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM musica ORDER BY artista ASC, titulo ASC"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_musica_paginados(page, por_pagina):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT id_musica, titulo, artista, anio, portada, audio
                FROM musica
                ORDER BY artista ASC, titulo ASC
                LIMIT ? OFFSET ?
            """
            offset = (page - 1) * por_pagina
            cursor.execute(sql, (por_pagina, offset))
            return cursor.fetchall()
    finally:
        conexion.close()


def contar_musica():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM musica")
            fila = cursor.fetchone()
            return fila["total"] if fila else 0
    finally:
        conexion.close()


def obtener_musica_por_id(id_musica):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM musica WHERE id_musica = ?"
            cursor.execute(sql, (id_musica,))
            return cursor.fetchone()
    finally:
        conexion.close()


def agregar_musica(datos):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO musica (titulo, artista, anio, descripcion, portada, audio)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["descripcion"],
                datos["portada"],
                datos["audio"],
            ))
            conexion.commit()
            return cursor.lastrowid
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_musica(id_musica, datos):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = """
                UPDATE musica
                SET titulo=?, artista=?, anio=?, descripcion=?, portada=?, audio=?
                WHERE id_musica=?
            """
            cursor.execute(sql, (
                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["descripcion"],
                datos["portada"],
                datos["audio"],
                id_musica,
            ))
            conexion.commit()
            return cursor.rowcount
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def eliminar_musica(id_musica):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = "DELETE FROM musica WHERE id_musica=?"
            cursor.execute(sql, (id_musica,))
            conexion.commit()
            return cursor.rowcount
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# ==========================================
# USUARIOS
# ==========================================

def obtener_usuario(usuario):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM usuarios
                WHERE usuario = ?
            """

            cursor.execute(sql, (usuario,))

            return cursor.fetchone()

    finally:

        conexion.close()