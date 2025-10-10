-- Crear tabla Movil
CREATE TABLE public.movil (
    nro_movil SERIAL PRIMARY KEY,
    descripcion_movil VARCHAR(100) NOT NULL,
    fecha_updated DATE NOT NULL,
    estado VARCHAR(100) DEFAULT 'Funcionando' CHECK (estado IN ('funcionando', 'reparar', 'disponible', 'ocupado')),
    color_mov VARCHAR(100) DEFAULT 'blue' CHECK (color_mov IN ('black', 'white', 'blue', 'red', 'green', 'brown', 'grey', 'pink', 'purple', 'orange', 'yellow', 'darkolive', 'lightpink', 'lightblue'))
);

-- Crear tabla UserProfile
CREATE TABLE public.user_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    profile_picture VARCHAR(100)
);

-- Crear tabla Conductor
CREATE TABLE public.conductor (
    id SERIAL PRIMARY KEY,
    nombre_conductor VARCHAR(100) NOT NULL
);

-- Crear tabla Agendamiento
CREATE TABLE public.agendamiento (
    id SERIAL PRIMARY KEY,
    descripcion_agendamiento VARCHAR(100) NOT NULL,
    movil_id INTEGER REFERENCES movil(nro_movil) ON DELETE CASCADE,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    usuario_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    conductor_id INTEGER REFERENCES conductor(id) ON DELETE SET NULL
);

CREATE TABLE public.lprdetecciones (
    id SERIAL PRIMARY KEY,
    ipAddress VARCHAR(255) NOT NULL,
    eventType VARCHAR(255) NOT NULL,
    licensePlate VARCHAR(255) NOT NULL,
    vehicleType VARCHAR(255) NOT NULL,
    confidenceLevel FLOAT NOT NULL,
    direction VARCHAR(255) NOT NULL,
    channelName VARCHAR(255) NOT NULL,
    licenseImage VARCHAR(255) NOT NULL,
    detectionImage VARCHAR(255) NOT NULL,
    dataTime TIMESTAMP NOT NULL
);
