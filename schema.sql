CREATE TABLE IF NOT EXISTS discos (
    id_disco INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    artista TEXT NOT NULL,
    anio TEXT,
    genero TEXT,
    sello TEXT,
    productor TEXT,
    duracion TEXT,
    descripcion TEXT,
    portada TEXT,
    escuchado INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS programas (
    id_programa INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER,
    fecha TEXT,
    observaciones TEXT,
    audio TEXT
);

CREATE TABLE IF NOT EXISTS programa_disco (
    id_programa INTEGER NOT NULL,
    id_disco INTEGER NOT NULL,
    PRIMARY KEY (id_programa, id_disco),
    FOREIGN KEY (id_programa) REFERENCES programas(id_programa),
    FOREIGN KEY (id_disco) REFERENCES discos(id_disco)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
