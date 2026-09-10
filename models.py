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


def obtener_generos_discos():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT DISTINCT genero
                FROM discos
                WHERE genero IS NOT NULL
                  AND TRIM(genero) <> ''
                ORDER BY genero ASC
            """

            cursor.execute(sql)

            return [fila["genero"] for fila in cursor.fetchall()]

    finally:
        conexion.close()


def _where_busqueda_discos():
    return """
        LOWER(d.titulo) LIKE LOWER(?)
        OR LOWER(d.artista) LIKE LOWER(?)
        OR LOWER(d.genero) LIKE LOWER(?)
        OR LOWER(d.sello) LIKE LOWER(?)
        OR LOWER(d.productor) LIKE LOWER(?)
    """


def _params_busqueda_discos(texto):
    busqueda = f"%{texto}%"
    return (busqueda, busqueda, busqueda, busqueda, busqueda)


def _where_y_params_discos(texto, stock, genero=None):
    clausulas = []
    params = []

    if texto:
        clausulas.append("( " + _where_busqueda_discos().strip() + " )")
        params += list(_params_busqueda_discos(texto))

    if stock in (0, 1):
        clausulas.append("d.en_stock = ?")
        params.append(stock)

    if genero:
        clausulas.append("d.genero = ?")
        params.append(genero)

    if not clausulas:
        return "", []

    return " WHERE " + " AND ".join(clausulas), params



def obtener_discos_paginados(page, por_pagina, texto=None, stock=None, genero=None):
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
                    d.en_stock,
                    d.id_musica,
                    m.audio AS musica_audio
                FROM discos d
                LEFT JOIN musica m ON d.id_musica = m.id_musica
            """

            where, params = _where_y_params_discos(texto, stock, genero)

            sql += where + " ORDER BY d.artista ASC, d.titulo ASC LIMIT ? OFFSET ?"

            offset = (page - 1) * por_pagina

            params += [por_pagina, offset]

            cursor.execute(sql, params)

            return cursor.fetchall()

    finally:
        conexion.close()


def contar_discos(texto=None, stock=None, genero=None):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = "SELECT COUNT(*) AS total FROM discos d"

            where, params = _where_y_params_discos(texto, stock, genero)

            sql += where

            cursor.execute(sql, params)

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
                    escuchado,
                    en_stock
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
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
                datos["en_stock"]

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
                    escuchado=?,
                    en_stock=?
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
                datos["en_stock"],
                id_disco

            ))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def actualizar_estado_stock(id_disco, valor):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = """
                UPDATE discos
                SET en_stock=?
                WHERE id_disco=?
            """

            cursor.execute(sql, (valor, id_disco))

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


def obtener_disco_vinculado_a_musica(id_musica):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM discos WHERE id_musica = ?
            """, (id_musica,))
            return cursor.fetchone()
    finally:
        conexion.close()


def vincular_disco_a_musica(id_disco, id_musica):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE discos SET id_musica = ? WHERE id_disco = ?
            """, (id_musica, id_disco))
            conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def desvincular_disco_de_musica(id_disco):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE discos SET id_musica = NULL WHERE id_disco = ?
            """, (id_disco,))
            conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
# ==========================================
# MUSICA
# ==========================================

def obtener_generos_musica():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT DISTINCT genero
                FROM musica
                WHERE genero IS NOT NULL
                  AND TRIM(genero) <> ''
                ORDER BY genero ASC
            """

            cursor.execute(sql)

            return [fila["genero"] for fila in cursor.fetchall()]

    finally:
        conexion.close()


def obtener_musica():
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM musica ORDER BY artista ASC, titulo ASC"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_musica_paginados(page, por_pagina, genero=None):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT id_musica, titulo, artista, anio, genero, portada, audio
                FROM musica
            """

            params = []

            if genero:
                sql += " WHERE genero = ?"
                params.append(genero)

            sql += " ORDER BY artista ASC, titulo ASC LIMIT ? OFFSET ?"

            offset = (page - 1) * por_pagina

            cursor.execute(sql, params + [por_pagina, offset])

            return cursor.fetchall()
    finally:
        conexion.close()


def contar_musica(genero=None):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:

            sql = "SELECT COUNT(*) AS total FROM musica"

            params = []

            if genero:
                sql += " WHERE genero = ?"
                params.append(genero)

            cursor.execute(sql, params)

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
                INSERT INTO musica (titulo, artista, anio, descripcion, portada, audio, genero)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (
                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["descripcion"],
                datos["portada"],
                datos["audio"],
                datos.get("genero"),
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
                SET titulo=?, artista=?, anio=?, descripcion=?, portada=?, audio=?, genero=?
                WHERE id_musica=?
            """
            cursor.execute(sql, (
                datos["titulo"],
                datos["artista"],
                datos["anio"],
                datos["descripcion"],
                datos["portada"],
                datos["audio"],
                datos.get("genero"),
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
# VIDEOS
# ==========================================

def obtener_videos_paginados(page, por_pagina):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT id_video, titulo, fecha, archivo_url, tipo_archivo
                FROM videos
                ORDER BY fecha DESC, id_video DESC
                LIMIT ? OFFSET ?
            """

            offset = (page - 1) * por_pagina

            cursor.execute(sql, (por_pagina, offset))

            return cursor.fetchall()

    finally:

        conexion.close()


def contar_videos():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            cursor.execute("SELECT COUNT(*) AS total FROM videos")

            fila = cursor.fetchone()

            return fila["total"] if fila else 0

    finally:

        conexion.close()


def obtener_video(id_video):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM videos
                WHERE id_video = ?
            """

            cursor.execute(sql, (id_video,))

            return cursor.fetchone()

    finally:

        conexion.close()


def agregar_video(datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                INSERT INTO videos
                (
                    titulo,
                    fecha,
                    archivo_url,
                    tipo_archivo
                )
                VALUES (?, ?, ?, ?)
            """

            cursor.execute(sql, (
                datos["titulo"],
                datos["fecha"],
                datos["archivo_url"],
                datos["tipo_archivo"]
            ))

            conexion.commit()

            return cursor.lastrowid

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def actualizar_video(id_video, datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                UPDATE videos
                SET
                    titulo=?,
                    fecha=?,
                    archivo_url=?,
                    tipo_archivo=?
                WHERE id_video=?
            """

            cursor.execute(sql, (
                datos["titulo"],
                datos["fecha"],
                datos["archivo_url"],
                datos["tipo_archivo"],
                id_video
            ))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def eliminar_video(id_video):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                DELETE FROM videos
                WHERE id_video=?
            """

            cursor.execute(sql, (id_video,))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


# ==========================================
# PELICULAS
# ==========================================

def obtener_generos_peliculas():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT DISTINCT genero
                FROM peliculas
                WHERE genero IS NOT NULL
                  AND TRIM(genero) <> ''
                ORDER BY genero ASC
            """

            cursor.execute(sql)

            return [fila["genero"] for fila in cursor.fetchall()]

    finally:
        conexion.close()


def obtener_peliculas_paginados(page, por_pagina, genero=None):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT id_pelicula, titulo, director, genero, portada, url_pelicula, url_subtitulos
                FROM peliculas
            """

            params = []

            if genero:
                sql += " WHERE genero = ?"
                params.append(genero)

            sql += " ORDER BY titulo ASC, id_pelicula ASC LIMIT ? OFFSET ?"

            offset = (page - 1) * por_pagina

            cursor.execute(sql, params + [por_pagina, offset])

            return cursor.fetchall()

    finally:
        conexion.close()


def contar_peliculas(genero=None):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = "SELECT COUNT(*) AS total FROM peliculas"

            params = []

            if genero:
                sql += " WHERE genero = ?"
                params.append(genero)

            cursor.execute(sql, params)

            fila = cursor.fetchone()

            return fila["total"] if fila else 0

    finally:
        conexion.close()


def obtener_pelicula(id_pelicula):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM peliculas
                WHERE id_pelicula = ?
            """

            cursor.execute(sql, (id_pelicula,))

            return cursor.fetchone()

    finally:
        conexion.close()


def agregar_pelicula(datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                INSERT INTO peliculas
                (
                    titulo,
                    director,
                    genero,
                    portada,
                    url_pelicula,
                    url_subtitulos
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """

            cursor.execute(sql, (
                datos["titulo"],
                datos["director"],
                datos["genero"],
                datos["portada"],
                datos["url_pelicula"],
                datos["url_subtitulos"]
            ))

            conexion.commit()

            return cursor.lastrowid

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def actualizar_pelicula(id_pelicula, datos):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                UPDATE peliculas
                SET
                    titulo=?,
                    director=?,
                    genero=?,
                    portada=?,
                    url_pelicula=?,
                    url_subtitulos=?
                WHERE id_pelicula=?
            """

            cursor.execute(sql, (
                datos["titulo"],
                datos["director"],
                datos["genero"],
                datos["portada"],
                datos["url_pelicula"],
                datos["url_subtitulos"],
                id_pelicula
            ))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def eliminar_pelicula(id_pelicula):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                DELETE FROM peliculas
                WHERE id_pelicula=?
            """

            cursor.execute(sql, (id_pelicula,))

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


def actualizar_password(id_usuario, nuevo_hash):
    conexion = get_connection()

    try:

        with conexion.cursor() as cursor:

            sql = "UPDATE usuarios SET password = ? WHERE id_usuario = ?"

            cursor.execute(sql, (nuevo_hash, id_usuario))

            conexion.commit()

            return cursor.rowcount

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


# ==========================================
# MIGRACIONES LIGERAS
# ==========================================

def _tabla_tiene_columna(conexion, tabla, columna):
    from database import DB_DRIVER

    with conexion.cursor() as cursor:
        if DB_DRIVER == "postgresql":
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (tabla, columna))
        else:
            cursor.execute(f"PRAGMA table_info({tabla})")
            filas = cursor.fetchall()

            for fila in filas:
                if (fila["name"] if "name" in fila.keys() else fila[1]) == columna:
                    return True

            return False

        fila = cursor.fetchone()
        return bool(fila and fila["count"] > 0)


def _existe_tabla(conexion, tabla):
    from database import DB_DRIVER

    with conexion.cursor() as cursor:
        if DB_DRIVER == "postgresql":
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (tabla,)
            )
        else:
            cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (tabla,)
            )
        return bool(cursor.fetchone())


def asegurar_columnas():
    """Agrega columnas faltantes y renombra tablas antiguas (sqlite y postgres)."""

    conexion = get_connection()

    try:
        if not _tabla_tiene_columna(conexion, "musica", "genero"):
            with conexion.cursor() as cursor:
                cursor.execute("ALTER TABLE musica ADD COLUMN genero TEXT")
            conexion.commit()

        if _existe_tabla(conexion, "entrevistas") and not _existe_tabla(conexion, "videos"):
            with conexion.cursor() as cursor:
                cursor.execute("ALTER TABLE entrevistas RENAME TO videos")
            conexion.commit()

        if _existe_tabla(conexion, "videos") and not _tabla_tiene_columna(conexion, "videos", "id_video"):
            with conexion.cursor() as cursor:
                cursor.execute("ALTER TABLE videos RENAME COLUMN id_entrevista TO id_video")
            conexion.commit()
    finally:
        conexion.close()


# ==========================================
# BUSQUEDA GLOBAL
# ==========================================

def buscar_global(texto):
    from database import DB_DRIVER

    conexion = get_connection()
    busqueda = f"%{texto}%"
    limite = 6

    try:
        resultados = {
            "discos": [],
            "musica": [],
            "peliculas": [],
            "programas": [],
            "videos": [],
        }

        with conexion.cursor() as cursor:

            cursor.execute(f"""
                SELECT d.id_disco, d.titulo, d.artista, d.genero, d.portada
                FROM discos d
                WHERE LOWER(d.titulo) LIKE LOWER(?)
                   OR LOWER(d.artista) LIKE LOWER(?)
                   OR LOWER(d.genero) LIKE LOWER(?)
                ORDER BY d.artista ASC, d.titulo ASC
                LIMIT ?
            """, (busqueda, busqueda, busqueda, limite))
            resultados["discos"] = cursor.fetchall()

            cursor.execute(f"""
                SELECT m.id_musica, m.titulo, m.artista, m.genero, m.portada
                FROM musica m
                WHERE LOWER(m.titulo) LIKE LOWER(?)
                   OR LOWER(m.artista) LIKE LOWER(?)
                   OR LOWER(m.genero) LIKE LOWER(?)
                ORDER BY m.artista ASC, m.titulo ASC
                LIMIT ?
            """, (busqueda, busqueda, busqueda, limite))
            resultados["musica"] = cursor.fetchall()

            cursor.execute(f"""
                SELECT p.id_pelicula, p.titulo, p.director, p.genero, p.portada
                FROM peliculas p
                WHERE LOWER(p.titulo) LIKE LOWER(?)
                   OR LOWER(p.director) LIKE LOWER(?)
                   OR LOWER(p.genero) LIKE LOWER(?)
                ORDER BY p.titulo ASC
                LIMIT ?
            """, (busqueda, busqueda, busqueda, limite))
            resultados["peliculas"] = cursor.fetchall()

            cursor.execute(f"""
                SELECT pr.id_programa, pr.numero, pr.fecha, pr.observaciones, pr.audio
                FROM programas pr
                WHERE CAST(pr.numero AS TEXT) LIKE ?
                   OR LOWER(pr.observaciones) LIKE LOWER(?)
                ORDER BY pr.fecha DESC
                LIMIT ?
            """, (busqueda, busqueda, limite))
            resultados["programas"] = cursor.fetchall()

            cursor.execute(f"""
                SELECT v.id_video, v.titulo, v.fecha, v.archivo_url, v.tipo_archivo
                FROM videos v
                WHERE LOWER(v.titulo) LIKE LOWER(?)
                ORDER BY v.fecha DESC, v.id_video DESC
                LIMIT ?
            """, (busqueda, limite))
            resultados["videos"] = cursor.fetchall()

        return resultados

    finally:
        conexion.close()