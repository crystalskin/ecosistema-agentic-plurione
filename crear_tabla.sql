-- Crear la tabla para almacenar el historial de interacciones
CREATE TABLE logs_interacciones (
    id_interaccion UUID PRIMARY KEY,
    modulo_origen VARCHAR(50) NOT NULL, -- chatbot, resolutor, sentimiento
    fecha_interaccion TIMESTAMP WITH TIME ZONE NOT NULL, -- El timestamp del JSON
    resultado VARCHAR(10) NOT NULL, -- EXITOSO o FALLIDO
    paso_fallido VARCHAR(100), -- Puede ser NULL si todo salió bien
    sentimiento_final VARCHAR(10) NOT NULL, -- POSITIVO, NEUTRAL, NEGATIVO
    fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Cuándo lo guardó tu módulo 7
);