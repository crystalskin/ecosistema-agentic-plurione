"""
====================================================================
AC-08: VALIDACIÓN Y ROLLBACK AUTOMÁTICO
Sistema de Aprendizaje Continuo Basado en Interacciones
====================================================================

Objetivo:
  1. Buscar el modelo CANDIDATO en MLflow (dejado por AC-06)
  2. Buscar el modelo ACTIVO actual (si existe)
  3. Evaluar AMBOS con los mismos datos de prueba
  4. Comparar métricas y decidir: promover o rechazar
  5. Actualizar tags en MLflow según la decisión
  6. Permitir rollback manual si se solicita

Autor: Alejandro José Núñez Velásquez
Empresa: PluriOne S.A. de C.V. — Develop Talent & Technology
====================================================================
"""

import os
import json
import shutil
import tempfile
import mlflow
import numpy as np
import torch
import subprocess
from pathlib import Path
from datetime import datetime
from mlflow import MlflowClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from peft import PeftModel
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import requests
import zipfile
import shutil


# =====================================================================
# 1. CONFIGURACIÓN
# =====================================================================

MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "AC06_FineTuning_IntencionClasificador"
DATASETS_DIR = Path("./datasets_ac05")
MODEL_BASE = "distilbert-base-uncased"

LABEL_MAP = {
    "consulta_saldo": 0,
    "cambio_plan": 1,
    "cancelacion_servicio": 2,
    "reclamo_facturacion": 3,
    "problema_tecnico": 4,
    "solicitar_humano": 5,
    "info_productos": 6,
    "otro": 7,
}
LABEL_MAP_INV = {v: k for k, v in LABEL_MAP.items()}

# --- Umbrales de decisión ---
MIN_ACCURACY_PROMOTE = 0.55
TOLERANCIA_DEGRADACION = 0.05

CAMPO_TEXTO = "texto_usuario"
CAMPO_ETIQUETA = "intencion"


# =====================================================================
# 2. CARGA DE DATOS DE EVALUACIÓN
# =====================================================================

def cargar_datos_evaluacion():
    """Carga datos para evaluar los modelos."""
    print("\n" + "=" * 60)
    print("  FASE 1: CARGAR DATOS DE EVALUACIÓN")
    print("=" * 60)

    archivos_val = list(DATASETS_DIR.glob("*val*.jsonl"))
    archivos_test = list(DATASETS_DIR.glob("*test*.jsonl"))
    archivos_todos = list(DATASETS_DIR.glob("*.jsonl"))

    archivos = archivos_val + archivos_test
    if not archivos:
        archivos = archivos_todos

    if not archivos:
        raise FileNotFoundError(
            f"No hay archivos .jsonl en {DATASETS_DIR}. "
            f"Ejecuta AC-05 o generar_datos_prueba.py primero."
        )

    datos = []
    for arch in archivos:
        with open(arch, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    d = json.loads(linea)
                    if CAMPO_TEXTO in d and CAMPO_ETIQUETA in d:
                        if d[CAMPO_ETIQUETA] in LABEL_MAP:
                            datos.append(d)

    print(f"  📊 Muestras cargadas: {len(datos)}")

    if len(datos) == 0:
        raise ValueError("El dataset de evaluación está vacío.")

    return datos


# =====================================================================
# 3. CONEXIÓN CON MLFLOW
# =====================================================================

def conectar_mlflow():
    """Conecta con MLflow y devuelve cliente + experimento."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise RuntimeError(
            f"El experimento '{EXPERIMENT_NAME}' no existe. "
            f"Ejecuta AC-06 primero."
        )

    print(f"\n  🔗 MLflow: {MLFLOW_TRACKING_URI}")
    print(f"  📁 Experimento: {EXPERIMENT_NAME}")
    print(f"  🆔 ID: {experiment.experiment_id}")

    return client, experiment


# =====================================================================
# 4. BÚSQUEDA DE MODELOS EN MLFLOW
# =====================================================================

def buscar_candidato(client, experiment_id):
    """Busca el último run con status='candidato'."""
    print(f"\n{'=' * 60}")
    print(f"  FASE 2: BUSCAR MODELO CANDIDATO")
    print(f"{'=' * 60}")

    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="tags.status = 'candidato'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )

    if not runs:
        print(f"  ❌ No hay modelo con status 'candidato'")
        return None

    run = runs[0]
    fecha = datetime.fromtimestamp(
        run.info.start_time / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")

    print(f"  ✅ Candidato encontrado:")
    print(f"     Run ID: {run.info.run_id}")
    print(f"     Nombre: {run.data.tags.get('mlflow.runName', 'sin nombre')}")
    print(f"     Fecha:  {fecha}")

    return run


def buscar_activo(client, experiment_id):
    """Busca el run actual con status='activo'."""
    print(f"\n{'=' * 60}")
    print(f"  FASE 3: BUSCAR MODELO ACTIVO")
    print(f"{'=' * 60}")

    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="tags.status = 'activo'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )

    if not runs:
        print(f"  ℹ️  No hay modelo activo.")
        print(f"     Esta es la primera validación del sistema.")
        return None

    run = runs[0]
    fecha = datetime.fromtimestamp(
        run.info.start_time / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")

    print(f"  ✅ Modelo activo encontrado:")
    print(f"     Run ID: {run.info.run_id}")
    print(f"     Fecha de activación: {fecha}")

    return run


# =====================================================================
# 5. DESCARGA Y CARGA DE MODELOS
# =====================================================================

def descargar_modelo(run_id, experiment_id, destino):
    """Carga el modelo directamente desde la carpeta local modelos_storage."""
    storage_dir = Path("./modelos_storage")
    ruta_zip = storage_dir / f"{run_id}.zip"
    
    if not ruta_zip.exists():
        raise RuntimeError(f"ZIP no encontrado en: {ruta_zip}")
        
    print(f"     Cargando desde disco local...")
    
    # Descomprimir
    extract_dir = os.path.join(destino, "modelo_extraido")
    with zipfile.ZipFile(ruta_zip, 'r') as z:
        z.extractall(extract_dir)
        
    # Buscar adapter_config.json recursivamente (puede estar en subcarpeta)
    modelo_path = None
    for root, dirs, files in os.walk(extract_dir):
        if "adapter_config.json" in files:
            modelo_path = root
            break
            
    if not modelo_path:
        raise RuntimeError("El ZIP no contiene un modelo LoRA válido.")
        
    print(f"     ✅ Modelo descomprimido correctamente.")
    return modelo_path

def cargar_modelo_lora(ruta_modelo):
    """Carga un modelo LoRA desde una ruta local."""
    tokenizer = AutoTokenizer.from_pretrained(ruta_modelo)

    base_model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_BASE,
        num_labels=len(LABEL_MAP),
        id2label=LABEL_MAP_INV,
        label2id=LABEL_MAP,
    )

    modelo = PeftModel.from_pretrained(base_model, ruta_modelo)
    modelo.eval()

    return modelo, tokenizer

# =====================================================================
# 6. EVALUACIÓN DE MODELO
# =====================================================================

def evaluar_modelo(modelo, tokenizer, datos):
    """Evalúa un modelo y retorna métricas."""
    clasificador = pipeline(
        "text-classification",
        model=modelo,
        tokenizer=tokenizer,
        top_k=None,
        device="cpu",
    )

    textos = [d[CAMPO_TEXTO] for d in datos]
    reales = [LABEL_MAP[d[CAMPO_ETIQUETA]] for d in datos]
    predichas = []

    for texto in textos:
        resultado = clasificador(texto)[0]
        mejor = max(resultado, key=lambda x: x["score"])
        predichas.append(LABEL_MAP[mejor["label"]])

    accuracy = accuracy_score(reales, predichas)
    precision, recall, f1, _ = precision_recall_fscore_support(
        reales, predichas, average="macro", zero_division=0
    )

    return {
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
    }


def evaluar_run(client, run, datos, etiqueta, experiment_id):
    """Descarga, carga y evalúa un run completo."""
    print(f"\n  📥 Cargando modelo {etiqueta}...")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = descargar_modelo(run.info.run_id, experiment_id, tmp)
        modelo, tok = cargar_modelo_lora(ruta)
        metricas = evaluar_modelo(modelo, tok, datos)
        del modelo
        del tok

    print(f"  📊 Métricas del {etiqueta.upper()}:")
    for k, v in metricas.items():
        print(f"     {k:<25} {v:.4f}")

    return metricas


# =====================================================================
# 7. LÓGICA DE DECISIÓN
# =====================================================================

def tomar_decision(metricas_cand, metricas_activo):
    """Decide si promover, rechazar o hacer rollback."""
    print(f"\n{'=' * 60}")
    print(f"  FASE 6: ANÁLISIS COMPARATIVO Y DECISIÓN")
    print(f"{'=' * 60}")

    # Tabla comparativa
    if metricas_activo:
        print(f"\n  {'Métrica':<25} {'Candidato':>12} {'Activo':>12} {'Dif':>12}")
        print(f"  {'─' * 25} {'─' * 12} {'─' * 12} {'─' * 12}")
        for k in metricas_cand:
            diff = metricas_cand[k] - metricas_activo[k]
            signo = "+" if diff > 0 else ""
            print(
                f"  {k:<25} "
                f"{metricas_cand[k]:>12.4f} "
                f"{metricas_activo[k]:>12.4f} "
                f"{signo}{diff:>11.4f}"
            )
    else:
        print(f"\n  (Sin modelo activo para comparar)")

    # Decisión
    if metricas_activo is None:
        if metricas_cand["accuracy"] >= MIN_ACCURACY_PROMOTE:
            return "PROMOVER", (
                f"Primera validación. Accuracy {metricas_cand['accuracy']:.4f} "
                f">= umbral {MIN_ACCURACY_PROMOTE}"
            )
        else:
            return "RECHAZAR", (
                f"Primera validación. Accuracy {metricas_cand['accuracy']:.4f} "
                f"< umbral {MIN_ACCURACY_PROMOTE}"
            )

    mejora_f1 = metricas_cand["f1_macro"] - metricas_activo["f1_macro"]
    degradacion_acc = metricas_activo["accuracy"] - metricas_cand["accuracy"]

    if mejora_f1 > 0 and degradacion_acc <= TOLERANCIA_DEGRADACION:
        return "PROMOVER", (
            f"F1 mejoró +{mejora_f1:.4f} sin degradar "
            f"accuracy más de {TOLERANCIA_DEGRADACION}"
        )
    elif mejora_f1 > 0.02 and degradacion_acc <= TOLERANCIA_DEGRADACION * 2:
        return "PROMOVER_OBSERVADO", (
            f"F1 mejoró +{mejora_f1:.4f} pero accuracy "
            f"degradó {degradacion_acc:.4f}"
        )
    else:
        return "RECHAZAR_ROLLBACK", (
            f"F1 {'no mejoró' if mejora_f1 <= 0 else 'mejoró poco'} "
            f"(+{mejora_f1:.4f}). Se mantiene modelo activo."
        )


# =====================================================================
# 8. EJECUTAR DECISIÓN EN MLFLOW
# =====================================================================

def ejecutar_decision(client, run_cand, run_activo, decision, razon, metricas_cand, metricas_activo):
    """Actualiza los tags en MLflow según la decisión."""
    print(f"\n{'=' * 60}")
    print(f"  FASE 7: EJECUTAR DECISIÓN EN MLFLOW")
    print(f"{'=' * 60}")

    ahora = datetime.now().isoformat()

    if decision in ("PROMOVER", "PROMOVER_OBSERVADO"):
        # Desactivar modelo anterior
        if run_activo:
            client.set_tag(run_activo.info.run_id, "status", "inactivo")
            client.set_tag(run_activo.info.run_id, "fecha_desactivacion", ahora)
            print(
                f"  🔄 Modelo anterior {run_activo.info.run_id[:8]}... "
                f"→ INACTIVO"
            )

        # Promover candidato
        client.set_tag(run_cand.info.run_id, "status", "activo")
        client.set_tag(run_cand.info.run_id, "fecha_activacion", ahora)
        client.set_tag(run_cand.info.run_id, "decision", decision)
        client.set_tag(run_cand.info.run_id, "decision_razon", razon)

        # Registrar métricas de validación
        with mlflow.start_run(run_id=run_cand.info.run_id):
            for k, v in metricas_cand.items():
                mlflow.log_metric(f"validacion_{k}", v)
            if metricas_activo:
                for k, v in metricas_activo.items():
                    mlflow.log_metric(f"baseline_activo_{k}", v)

        print(
            f"  ✅ Modelo {run_cand.info.run_id[:8]}... → ACTIVO"
        )
        if decision == "PROMOVER_OBSERVADO":
            print(f"  ⚠️  Promovido con observación (accuracy degradó)")
        else:
            print(f"  🎉 Promoción limpia")

    elif decision == "RECHAZAR":
        client.set_tag(run_cand.info.run_id, "status", "rechazado")
        client.set_tag(run_cand.info.run_id, "decision", "rechazado")
        client.set_tag(run_cand.info.run_id, "decision_razon", razon)
        print(
            f"  ❌ Modelo {run_cand.info.run_id[:8]}... → RECHAZADO"
        )
        print(f"     No cumple umbral mínimo de calidad.")

    elif decision == "RECHAZAR_ROLLBACK":
        client.set_tag(run_cand.info.run_id, "status", "rechazado_rollback")
        client.set_tag(run_cand.info.run_id, "decision", "rollback_automatico")
        client.set_tag(run_cand.info.run_id, "decision_razon", razon)
        print(f"  ⏪ ROLLBACK AUTOMÁTICO ejecutado")
        print(
            f"  ❌ Modelo {run_cand.info.run_id[:8]}... → RECHAZADO"
        )
        print(
            f"  ✅ Modelo activo {run_activo.info.run_id[:8]}... "
            f"se MANTIENE"
        )


# =====================================================================
# 9. ROLLBACK MANUAL
# =====================================================================

def rollback_manual(client, experiment_id):
    """Permite hacer rollback manual a un modelo anterior."""
    print(f"\n{'=' * 60}")
    print(f"  🔄 ROLLBACK MANUAL")
    print(f"{'=' * 60}")

    # Buscar modelo activo actual
    activos = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="tags.status = 'activo'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )

    # Buscar modelos inactivos
    inactivos = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string="tags.status = 'inactivo'",
        order_by=["attribute.start_time DESC"],
    )

    if not activos:
        print(f"  ❌ No hay modelo activo para hacer rollback.")
        return

    if not inactivos:
        print(f"  ❌ No hay modelos anteriores para restaurar.")
        return

    run_activo = activos[0]
    ahora = datetime.now().isoformat()

    # Desactivar actual
    client.set_tag(run_activo.info.run_id, "status", "inactivo")
    client.set_tag(run_activo.info.run_id, "fecha_desactivacion", ahora)
    print(f"  🔄 Modelo activo {run_activo.info.run_id[:8]}... → INACTIVO")

    # Activar el más reciente inactivo
    run_restaurar = inactivos[0]
    client.set_tag(run_restaurar.info.run_id, "status", "activo")
    client.set_tag(run_restaurar.info.run_id, "fecha_activacion", ahora)
    client.set_tag(run_restaurar.info.run_id, "decision", "rollback_manual")

    print(f"  ✅ Modelo {run_restaurar.info.run_id[:8]}... → ACTIVO")
    print(f"     Tipo: ROLLBACK MANUAL")

    fecha = datetime.fromtimestamp(
        run_restaurar.info.start_time / 1000
    ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"     Modelo original entrenado: {fecha}")


# =====================================================================
# 10. FUNCIÓN PRINCIPAL
# =====================================================================

def main(modo="auto"):
    """Ejecución principal de AC-08."""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║  AC-08: VALIDACIÓN Y ROLLBACK AUTOMÁTICO               ║")
    print("║  Sistema de Aprendizaje Continuo                       ║")
    print("║  PluriOne S.A. de C.V. — Develop Talent & Technology   ║")
    print("╚" + "═" * 58 + "╝")

    try:
        client, experiment = conectar_mlflow()

        # Modo rollback manual
        if modo == "rollback":
            rollback_manual(client, experiment.experiment_id)
            print(f"\n  ✅ ROLLBACK MANUAL COMPLETADO\n")
            return

        # Buscar candidato
        run_cand = buscar_candidato(client, experiment.experiment_id)
        if run_cand is None:
            print(f"\n  ⛔ No hay candidato que validar.")
            print(f"     Ejecuta AC-06 primero para entrenar uno.\n")
            return

        # Buscar activo
        run_activo = buscar_activo(client, experiment.experiment_id)

        # Cargar datos
        datos = cargar_datos_evaluacion()

        # Evaluar candidato (FASE 4)
        print(f"\n{'=' * 60}")
        print(f"  FASE 4: EVALUAR MODELO CANDIDATO")
        print(f"{'=' * 60}")
        metricas_cand = evaluar_run(client, run_cand, datos, "candidato", experiment.experiment_id)

        # Evaluar activo (FASE 5)
        metricas_activo = None
        if run_activo:
            print(f"\n{'=' * 60}")
            print(f"  FASE 5: EVALUAR MODELO ACTIVO")
            print(f"{'=' * 60}")
            metricas_activo = evaluar_run(client, run_activo, datos, "activo", experiment.experiment_id)

        # Decisión
        decision, razon = tomar_decision(metricas_cand, metricas_activo)

        print(f"\n  ⚖️  DECISIÓN: {decision}")
        print(f"  📝 Razón: {razon}")

        # Ejecutar
        ejecutar_decision(
            client, run_cand, run_activo,
            decision, razon, metricas_cand, metricas_activo
        )

        # Resumen
        estado = "ACTIVO" if "PROMOVER" in decision else "RECHAZADO"
        print(f"\n╔" + "═" * 58 + "╗")
        print(f"║  ✅ AC-08 COMPLETADO                               ║")
        print(f"╠" + "═" * 58 + "╣")
        print(f"║  Decisión:   {decision:<42}║")
        print(f"║  Modelo:     {estado:<42}║")
        print(f"║  Accuracy:   {metricas_cand['accuracy']:.4f}{' ' * 34}║")
        print(f"║  F1 Macro:   {metricas_cand['f1_macro']:.4f}{' ' * 34}║")
        print(f"╚" + "═" * 58 + "╝\n")

    except Exception as e:
        print(f"\n  ❌ ERROR FATAL EN AC-08: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    modo = "auto"
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        modo = "rollback"
    main(modo)