from database import get_connection


# ==========================================
# DISCOS
# ==========================================

def obtener_discos():
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM discos
                ORDER BY artista ASC, titulo ASC
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
                SELECT *
                FROM discos
                WHERE id_disco = %s
            """

            cursor.execute(sql, (id_disco,))

            return cursor.fetchone()

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
                    escuchado
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                    titulo=%s,
                    artista=%s,
                    anio=%s,
                    genero=%s,
                    sello=%s,
                    productor=%s,
                    duracion=%s,
                    descripcion=%s,
                    portada=%s,
                    escuchado=%s
                WHERE id_disco=%s
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
                WHERE id_disco=%s
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
                WHERE titulo LIKE %s
                   OR artista LIKE %s
                   OR genero LIKE %s
                   OR sello LIKE %s
                   OR productor LIKE %s
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


def obtener_programa(id_programa):
    conexion = get_connection()

    try:
        with conexion.cursor() as cursor:

            sql = """
                SELECT *
                FROM programas
                WHERE id_programa = %s
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
                    %s,
                    %s,
                    %s,
                    %s
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
                    numero=%s,
                    fecha=%s,
                    observaciones=%s,
                    audio=%s
                WHERE id_programa=%s
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
                WHERE id_programa=%s
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
                WHERE escuchado = FALSE
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
                    %s,
                    %s
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
                WHERE id_programa=%s
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
                WHERE id_programa=%s
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
                SET escuchado = TRUE
                WHERE id_disco = %s
            """

            cursor.execute(sql, (id_disco,))

            conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()