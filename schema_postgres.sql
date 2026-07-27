CREATE TABLE IF NOT EXISTS discos (
    id_disco SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    artista VARCHAR(255) NOT NULL,
    anio VARCHAR(10),
    genero VARCHAR(100),
    sello VARCHAR(255),
    productor VARCHAR(255),
    duracion VARCHAR(20),
    descripcion TEXT,
    portada VARCHAR(255),
    escuchado INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS programas (
    id_programa SERIAL PRIMARY KEY,
    numero INTEGER,
    fecha VARCHAR(20),
    observaciones TEXT,
    audio VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS programa_disco (
    id_programa INTEGER NOT NULL REFERENCES programas(id_programa),
    id_disco INTEGER NOT NULL REFERENCES discos(id_disco),
    PRIMARY KEY (id_programa, id_disco)
);

CREATE TABLE IF NOT EXISTS musica (
    id_musica SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    artista VARCHAR(255) NOT NULL,
    anio VARCHAR(10),
    descripcion TEXT,
    portada VARCHAR(255),
    audio VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
