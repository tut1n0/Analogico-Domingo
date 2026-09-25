POR_PAGINA = 20
ANIO_MINIMO = 1950

DECADAS = (
    {"etiqueta": "90-00", "minimo": 1990, "maximo": 2000},
    {"etiqueta": "80-70", "minimo": 1970, "maximo": 1980},
    {"etiqueta": "70-60", "minimo": 1960, "maximo": 1970},
    {"etiqueta": "60-50", "minimo": 1950, "maximo": 1960},
    {"etiqueta": "50-40", "minimo": 1950, "maximo": 1959},
)


def obtener_rango_decada(valor):
    if not valor:
        return None

    return next((rango for rango in DECADAS if rango["etiqueta"] == valor), None)
