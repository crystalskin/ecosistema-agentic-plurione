"""
generador_dataset.py — AC-05: Sistema de Aprendizaje Continuo
Construye datasets curados y versionados para re-entrenamiento.

Genera dos archivos JSONL:
  - dataset_positivos_vX.jsonl  → Interacciones EXITOSAS (ejemplos de buenas respuestas)
  - dataset_correcciones_vX.jsonl → Interacciones FALLIDAS (qué debió responder el agente)

Formato JSONL estándar para fine-tuning:
  {"prompt": "<texto_usuario>", "completion": "<respuesta_ideal>", "metadata": {...}}

Corre con: python generador_dataset.py
"""

import psycopg2
import json
import os
from datetime import datetime, timezone

# ── Configuración ────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "database": "aprendizaje_db",
    "user":     "usuario_learning",
    "password": "password_secreto",
    "port":     "5432"
}
DIRECTORIO_DATASETS = "./datasets"

# Respuestas corregidas por tipo de error
# En producción esto vendría de una interfaz de revisión humana.
# Por ahora usamos correcciones predefinidas por categoría.
CORRECCIONES_POR_ERROR = {
    "FALLO_ENTRENAMIENTO_NLP": (
        "Entiendo que tienes una consulta. ¿Podrías indicarme si tu solicitud es "
        "sobre: (1) tu cuenta, (2) un pago, (3) soporte técnico o (4) cancelación? "
        "Así puedo ayudarte mejor."
    ),
    "FRUSTRACION_CLIENTE": (
        "Entiendo tu frustración y me disculpo por los inconvenientes. "
        "Te comunico de inmediato con un especialista que podrá resolver tu caso de forma prioritaria."
    ),
    "FALLO_INTEGRACION_TECNICA": (
        "Estoy teniendo dificultades para acceder a esa información en este momento. "
        "He registrado tu solicitud y un agente se comunicará contigo en menos de 2 horas "
        "con la información que necesitas."
    ),
    "CAUSA_DESCONOCIDA": (
        "Lo siento, en este momento no puedo procesar tu solicitud correctamente. "
        "¿Te gustaría que te transfiriera con un agente humano para ayudarte?"
    ),
}

def conectar_db():
    return psycopg2.connect(**DB_CONFIG)

def obtener_version_siguiente():
    """Lee la versión más alta existente y devuelve la siguiente."""
    os.makedirs(DIRECTORIO_DATASETS, exist_ok=True)
    archivos = [f for f in os.listdir(DIRECTORIO_DATASETS) if f.endswith(".jsonl")]
    versiones = []
    for f in archivos:
        partes = f.replace(".jsonl", "").split("_v")
        if len(partes) == 2 and partes[1].isdigit():
            versiones.append(int(partes[1]))
    return max(versiones, default=0) + 1

def construir_dataset_positivos(cursor, version):
    """
    Extrae interacciones EXITOSAS con texto real.
    Estas serán los ejemplos positivos del dataset.
    """
    cursor.execute("""
        SELECT 
            id_interaccion,
            modulo_origen,
            texto_usuario,
            respuesta_agente,
            sentimiento_final,
            fecha_interaccion
        FROM logs_interacciones
        WHERE resultado = 'EXITOSO'
          AND texto_usuario IS NOT NULL
          AND respuesta_agente IS NOT NULL
          AND incluido_en_dataset = FALSE
        ORDER BY fecha_interaccion DESC;
    """)
    filas = cursor.fetchall()

    if not filas:
        print("  ⚠️  No hay interacciones EXITOSAS nuevas con texto para procesar.")
        return [], []

    registros  = []
    ids_vistos = []

    for fila in filas:
        id_int, origen, texto, respuesta, sentimiento, fecha = fila
        registro = {
            "prompt":     texto.strip(),
            "completion": respuesta.strip(),
            "tipo":       "positivo",
            "metadata": {
                "id_interaccion":  str(id_int),
                "modulo_origen":   origen,
                "sentimiento":     sentimiento,
                "fecha":           fecha.isoformat(),
                "dataset_version": version,
            }
        }
        registros.append(registro)
        ids_vistos.append(str(id_int))

    return registros, ids_vistos

def construir_dataset_correcciones(cursor, version):
    """
    Extrae interacciones FALLIDAS con clasificación de error.
    Asigna la corrección esperada según el tipo de fallo.
    """
    cursor.execute("""
        SELECT 
            id_interaccion,
            modulo_origen,
            texto_usuario,
            respuesta_agente,
            clasificacion_error,
            paso_fallido,
            sentimiento_final,
            fecha_interaccion
        FROM logs_interacciones
        WHERE resultado = 'FALLIDO'
          AND texto_usuario IS NOT NULL
          AND clasificacion_error IS NOT NULL
          AND incluido_en_dataset = FALSE
        ORDER BY fecha_interaccion DESC;
    """)
    filas = cursor.fetchall()

    if not filas:
        print("  ⚠️  No hay interacciones FALLIDAS nuevas con texto para procesar.")
        return [], []

    registros  = []
    ids_vistos = []

    for fila in filas:
        id_int, origen, texto, respuesta_incorrecta, clasificacion, paso_fallido, sentimiento, fecha = fila
        correccion = CORRECCIONES_POR_ERROR.get(clasificacion, CORRECCIONES_POR_ERROR["CAUSA_DESCONOCIDA"])

        registro = {
            "prompt":               texto.strip(),
            "completion":           correccion,
            "respuesta_incorrecta": respuesta_incorrecta.strip() if respuesta_incorrecta else None,
            "tipo":                 "correccion",
            "metadata": {
                "id_interaccion":    str(id_int),
                "modulo_origen":     origen,
                "clasificacion":     clasificacion,
                "paso_fallido":      paso_fallido,
                "sentimiento":       sentimiento,
                "fecha":             fecha.isoformat(),
                "dataset_version":   version,
            }
        }
        registros.append(registro)
        ids_vistos.append(str(id_int))

    return registros, ids_vistos

def guardar_jsonl(registros, nombre_archivo):
    """Guarda una lista de registros en formato JSONL (un JSON por línea)."""
    ruta = os.path.join(DIRECTORIO_DATASETS, nombre_archivo)
    with open(ruta, 'w', encoding='utf-8') as f:
        for registro in registros:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')
    return ruta

def marcar_como_incluidos(cursor, ids):
    """Marca los registros procesados para no incluirlos en el próximo ciclo."""
    if not ids:
        return
    placeholders = ','.join(['%s'] * len(ids))
    cursor.execute(
        f"UPDATE logs_interacciones SET incluido_en_dataset = TRUE WHERE id_interaccion::text IN ({placeholders});",
        ids
    )

def guardar_metadata_ciclo(version, positivos, correcciones, ids_procesados):
    """Guarda un archivo de metadata del ciclo para trazabilidad."""
    metadata = {
        "version":           version,
        "fecha_generacion":  datetime.now(timezone.utc).isoformat(),
        "total_registros":   len(ids_procesados),
        "positivos":         len(positivos),
        "correcciones":      len(correcciones),
        "ids_procesados":    ids_procesados,
        "archivos_generados": {
            "positivos":    f"dataset_positivos_v{version}.jsonl",
            "correcciones": f"dataset_correcciones_v{version}.jsonl",
        }
    }
    ruta = os.path.join(DIRECTORIO_DATASETS, f"metadata_v{version}.json")
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return ruta

# ── FUNCIÓN PRINCIPAL ────────────────────────────────────────────
def generar_dataset():
    print("=" * 60)
    print("  AC-05: Generador de Dataset Curado para Re-entrenamiento")
    print("=" * 60)

    version = obtener_version_siguiente()
    print(f"\n📦 Generando dataset versión v{version}...")
    print(f"   Directorio de salida: {DIRECTORIO_DATASETS}/\n")

    conn   = conectar_db()
    cursor = conn.cursor()

    # ── Construir dataset de positivos ──────────────────────────
    print("📊 Procesando interacciones EXITOSAS...")
    positivos, ids_positivos = construir_dataset_positivos(cursor, version)
    print(f"   → {len(positivos)} ejemplos positivos encontrados.")

    # ── Construir dataset de correcciones ────────────────────────
    print("\n🔧 Procesando interacciones FALLIDAS...")
    correcciones, ids_correcciones = construir_dataset_correcciones(cursor, version)
    print(f"   → {len(correcciones)} correcciones generadas.")

    ids_totales = ids_positivos + ids_correcciones

    if not ids_totales:
        print("\n⚠️  No hay datos nuevos para procesar en este ciclo.")
        print("   Corre el simulador_mensajes.py para agregar datos de prueba.")
        cursor.close()
        conn.close()
        return

    # ── Guardar archivos JSONL ───────────────────────────────────
    print("\n💾 Guardando archivos de dataset...")
    if positivos:
        ruta_pos = guardar_jsonl(positivos, f"dataset_positivos_v{version}.jsonl")
        print(f"   ✅ {ruta_pos}")
    if correcciones:
        ruta_cor = guardar_jsonl(correcciones, f"dataset_correcciones_v{version}.jsonl")
        print(f"   ✅ {ruta_cor}")

    # ── Guardar metadata del ciclo ───────────────────────────────
    ruta_meta = guardar_metadata_ciclo(version, positivos, correcciones, ids_totales)
    print(f"   ✅ {ruta_meta}")

    # ── Marcar registros como procesados ─────────────────────────
    marcar_como_incluidos(cursor, ids_totales)
    conn.commit()
    print(f"\n   🔖 {len(ids_totales)} registros marcados como incluidos en dataset.")

    cursor.close()
    conn.close()

    # ── Resumen final ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  ✅ Dataset v{version} generado exitosamente")
    print("=" * 60)
    print(f"  📁 Total de registros procesados : {len(ids_totales)}")
    print(f"  ✅ Ejemplos positivos (EXITOSO)   : {len(positivos)}")
    print(f"  🔧 Correcciones (FALLIDO)         : {len(correcciones)}")
    print(f"  📂 Directorio                     : {DIRECTORIO_DATASETS}/")
    print("\n  ➡️  Siguiente paso: fine-tuning con estos datasets (AC-06)")
    print("=" * 60)

if __name__ == "__main__":
    generar_dataset()