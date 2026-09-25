POR_PAGINA = 20

DECADAS = (
    {"etiqueta": "90-00", "minimo": 1990, "maximo": 2000},
    {"etiqueta": "80-70", "minimo": 1970, "maximo": 1980},
    {"etiqueta": "70-60", "minimo": 1960, "maximo": 1970},
    {"etiqueta": "60-50", "minimo": 1950, "maximo": 1960},
    {"etiqueta": "50-40", "minimo": 1940, "maximo": 1950},
    {"etiqueta": "40-30", "minimo": 1930, "maximo": 1940},
    {"etiqueta": "30-20", "minimo": 1920, "maximo": 1930},
    {"etiqueta": "20-10", "minimo": 1910, "maximo": 1920},
    {"etiqueta": "10-00", "minimo": 1900, "maximo": 1910},
)


def obtener_rango_decada(valor):
    if not valor:
        return None

    return next((rango for rango in DECADAS if rango["etiqueta"] == valor), None)
