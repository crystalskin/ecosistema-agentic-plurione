"""
====================================================================
AC-06: FINE-TUNING DEL MODELO CON LORA
Sistema de Aprendizaje Continuo Basado en Interacciones
====================================================================

Objetivo:
  1. Cargar datasets .jsonl generados por AC-05
  2. Aplicar fine-tuning con técnica LoRA (PEFT) sobre DistilBERT
  3. Registrar experimento, métricas y modelo en MLflow (AC-11)
  4. Dejar el modelo como "candidato" hasta validar en AC-08

Autor: Alejandro José Núñez Velásquez
Empresa: PluriOne S.A. de C.V. — Develop Talent & Technology
====================================================================
"""

import os
import json
import mlflow
import shutil
import mlflow.transformers
import numpy as np
import torch
from pathlib import Path
from datetime import datetime
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    pipeline,
)
from peft import LoraConfig, get_peft_model, TaskType
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

# =====================================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================================

# --- Rutas ---
DATASETS_DIR = Path("./datasets_ac05")
MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "AC06_FineTuning_IntencionClasificador"

# --- Modelo base ---
MODEL_BASE = "distilbert-base-uncased"

# --- Mapa de intenciones ---
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
NUM_LABELS = len(LABEL_MAP)

# --- Hiperparámetros de entrenamiento ---
HYPERPARAMS = {
    "learning_rate": 2e-4,
    "num_train_epochs": 3,
    "per_device_train_batch_size": 8,
    "per_device_eval_batch_size": 8,
    "weight_decay": 0.01,
    "warmup_ratio": 0.1,
    "lr_scheduler_type": "cosine",
    "logging_steps": 10,
    "eval_strategy": "epoch",
    "save_strategy": "epoch",
    "load_best_model_at_end": True,
    "metric_for_best_model": "f1_macro",
    "greater_is_better": True,
}

# --- Configuración LoRA ---
LORA_CONFIG = {
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.1,
    "target_modules": ["q_lin", "v_lin"],
    "bias": "none",
    "task_type": TaskType.SEQ_CLS,
}

# --- Umbrales de calidad ---
MIN_TRAIN_SAMPLES = 30
MIN_ACCURACY = 0.55

# --- Nombres de campos en el .jsonl ---
CAMPO_TEXTO = "texto_usuario"
CAMPO_ETIQUETA = "intencion"


# =====================================================================
# 2. FUNCIONES DE CARGA DE DATOS
# =====================================================================

def cargar_jsonl(ruta_archivo):
    """Carga un archivo .jsonl y retorna lista de diccionarios."""
    datos = []
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                datos.append(json.loads(linea))
    return datos


def cargar_datasets(ruta_dir):
    """Carga los datasets de entrenamiento y validación desde AC-05."""
    print("\n" + "=" * 60)
    print("  FASE 1: CARGA DE DATOS (desde AC-05)")
    print("=" * 60)

    archivos = list(ruta_dir.glob("*.jsonl"))

    if not archivos:
        raise FileNotFoundError(
            f"\n  ❌ No se encontraron archivos .jsonl en: {ruta_dir}\n"
            f"  💡 Ejecuta primero: python generar_datos_prueba.py"
        )

    arch_train = None
    arch_val = None
    arch_todos = []

    for arch in archivos:
        nombre = arch.name.lower()
        if "train" in nombre:
            arch_train = arch
        elif "val" in nombre or "test" in nombre:
            arch_val = arch
        else:
            arch_todos.append(arch)

    if arch_train is None:
        if arch_todos:
            print(f"  📄 Cargando todos los archivos (sin separación train/val)")
            todos_datos = []
            for arch in arch_todos:
                print(f"     → {arch.name}")
                todos_datos.extend(cargar_jsonl(arch))
            np.random.seed(42)
            np.random.shuffle(todos_datos)
            split_idx = int(len(todos_datos) * 0.8)
            datos_train = todos_datos[:split_idx]
            datos_val = todos_datos[split_idx:]
        else:
            raise FileNotFoundError("No se encontraron archivos de entrenamiento.")
    else:
        print(f"  📄 Train: {arch_train.name}")
        datos_train = cargar_jsonl(arch_train)
        if arch_val:
            print(f"  📄 Val:   {arch_val.name}")
            datos_val = cargar_jsonl(arch_val)
        else:
            np.random.seed(42)
            np.random.shuffle(datos_train)
            split_idx = int(len(datos_train) * 0.8)
            datos_val = datos_train[split_idx:]
            datos_train = datos_train[:split_idx]

    datos_train = [d for d in datos_train if CAMPO_TEXTO in d and CAMPO_ETIQUETA in d]
    datos_val = [d for d in datos_val if CAMPO_TEXTO in d and CAMPO_ETIQUETA in d]

    etiquetas_conocidas = set(LABEL_MAP.keys())
    datos_train = [d for d in datos_train if d[CAMPO_ETIQUETA] in etiquetas_conocidas]
    datos_val = [d for d in datos_val if d[CAMPO_ETIQUETA] in etiquetas_conocidas]

    print(f"\n  ✅ Datos cargados y filtrados:")
    print(f"     Train: {len(datos_train)} muestras")
    print(f"     Val:   {len(datos_val)} muestras")
    print(f"     Labels: {NUM_LABELS} clases")

    if len(datos_train) < MIN_TRAIN_SAMPLES:
        raise ValueError(
            f"\n  ❌ Dataset insuficiente: {len(datos_train)} muestras\n"
            f"  Mínimo requerido: {MIN_TRAIN_SAMPLES}"
        )

    print(f"\n  📊 Distribución de clases (train):")
    conteo = {}
    for d in datos_train:
        etiqueta = d[CAMPO_ETIQUETA]
        conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
    for etiqueta, count in sorted(conteo.items(), key=lambda x: -x[1]):
        bar = "█" * (count * 2)
        print(f"     {etiqueta:<25} {count:>4} {bar}")

    return datos_train, datos_val


# =====================================================================
# 3. PREPARACIÓN DEL DATASET PARA HUGGINGFACE
# =====================================================================

def preparar_dataset_hf(datos_train, datos_val, tokenizer):
    """Convierte los datos a formato Dataset de HuggingFace y tokeniza."""
    print("\n" + "=" * 60)
    print("  FASE 2: TOKENIZACIÓN Y PREPARACIÓN")
    print("=" * 60)

    def formatear_registro(registro):
        return {
            "text": registro[CAMPO_TEXTO],
            "label": LABEL_MAP[registro[CAMPO_ETIQUETA]],
            "label_text": registro[CAMPO_ETIQUETA],
        }

    def tokenizar(ejemplos):
        return tokenizer(
            ejemplos["text"],
            truncation=True,
            max_length=128,
            padding=False,
        )

    train_formateado = [formatear_registro(d) for d in datos_train]
    val_formateado = [formatear_registro(d) for d in datos_val]

    ds_train = Dataset.from_list(train_formateado)
    ds_val = Dataset.from_list(val_formateado)

    print(f"  🔤 Tokenizando con: {MODEL_BASE}")
    ds_train = ds_train.map(tokenizar, batched=True, remove_columns=["text", "label_text"])
    ds_val = ds_val.map(tokenizar, batched=True, remove_columns=["text", "label_text"])

    dataset = DatasetDict({
        "train": ds_train,
        "validation": ds_val,
    })

    print(f"  ✅ Dataset preparado:")
    print(f"     Train:      {len(dataset['train'])} ejemplos")
    print(f"     Validation: {len(dataset['validation'])} ejemplos")

    return dataset


# =====================================================================
# 4. CONFIGURACIÓN DEL MODELO CON LORA
# =====================================================================

def crear_modelo_con_lora():
    """Carga el modelo base e inyecta adaptadores LoRA."""
    print("\n" + "=" * 60)
    print("  FASE 3: MODELO + LORA (PEFT)")
    print("=" * 60)

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  🖥️  Dispositivo: {dispositivo}")
    if dispositivo == "cuda":
        print(f"     GPU: {torch.cuda.get_device_name(0)}")

    print(f"\n  📥 Cargando tokenizer: {MODEL_BASE}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_BASE)

    print(f"  📥 Cargando modelo base: {MODEL_BASE}")
    modelo_base = AutoModelForSequenceClassification.from_pretrained(
        MODEL_BASE,
        num_labels=NUM_LABELS,
        id2label=LABEL_MAP_INV,
        label2id=LABEL_MAP,
    )

    params_total = sum(p.numel() for p in modelo_base.parameters())
    print(f"\n  📊 Modelo base:")
    print(f"     Parámetros totales: {params_total:,}")

    print(f"\n  🔧 Inyectando adaptadores LoRA...")
    print(f"     Rank (r):           {LORA_CONFIG['r']}")
    print(f"     Alpha:              {LORA_CONFIG['lora_alpha']}")
    print(f"     Dropout:            {LORA_CONFIG['lora_dropout']}")
    print(f"     Target modules:     {LORA_CONFIG['target_modules']}")

    lora_cfg = LoraConfig(**LORA_CONFIG)
    modelo_lora = get_peft_model(modelo_base, lora_cfg)

    params_trainable = sum(p.numel() for p in modelo_lora.parameters() if p.requires_grad)
    params_frozen = sum(p.numel() for p in modelo_lora.parameters() if not p.requires_grad)
    pct = (params_trainable / params_total) * 100

    print(f"\n  📊 Modelo con LoRA:")
    print(f"     Parámetros entrenables: {params_trainable:,} ({pct:.2f}%)")
    print(f"     Parámetros congelados:  {params_frozen:,} ({100 - pct:.2f}%)")
    print(f"     ✅ Reducción de {100 - pct:.1f}% en parámetros a entrenar")

    modelo_lora.print_trainable_parameters()

    return modelo_lora, tokenizer


# =====================================================================
# 5. MÉTRICAS DE EVALUACIÓN
# =====================================================================

def calcular_metricas(eval_pred):
    """Calcula métricas de clasificación para el Trainer."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    accuracy = accuracy_score(labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )
    precision_w, recall_w, f1_w, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted", zero_division=0
    )

    return {
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "precision_weighted": precision_w,
        "recall_weighted": recall_w,
        "f1_weighted": f1_w,
    }


# =====================================================================
# 6. ENTRENAMIENTO
# =====================================================================

def entrenar_modelo(modelo, tokenizer, dataset):
    """Ejecuta el ciclo de fine-tuning con LoRA."""
    print("\n" + "=" * 60)
    print("  FASE 4: FINE-TUNING CON LORA")
    print("=" * 60)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    output_dir = "./resultados_ac06"
    training_args = TrainingArguments(
        output_dir=output_dir,
        **HYPERPARAMS,
        report_to="none",
        fp16=torch.cuda.is_available(),
        seed=42,
    )

    print(f"  ⚙️  Hiperparámetros:")
    for k, v in HYPERPARAMS.items():
        print(f"     {k:<30} {v}")

    trainer = Trainer(
        model=modelo,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        data_collator=data_collator,
        compute_metrics=calcular_metricas,
    )

    print(f"\n  🚀 Iniciando entrenamiento...")
    print(f"     Epochs: {HYPERPARAMS['num_train_epochs']}")
    print(f"     Batch size: {HYPERPARAMS['per_device_train_batch_size']}")
    print()

    resultado = trainer.train()

    print(f"\n  ✅ Entrenamiento completado")

    print(f"\n  📊 Evaluación final en validación:")
    metricas_finales = trainer.evaluate()
    for metrica, valor in metricas_finales.items():
        if metrica.startswith("eval_"):
            nombre = metrica.replace("eval_", "")
            print(f"     {nombre:<25} {valor:.4f}")

    print(f"\n  📋 Reporte de clasificación detallado:")
    predicciones = trainer.predict(dataset["validation"])
    y_pred = np.argmax(predicciones.predictions, axis=-1)
    y_true = predicciones.label_ids

    print(classification_report(
        y_true, y_pred,
        target_names=[LABEL_MAP_INV[i] for i in range(NUM_LABELS)],
        zero_division=0,
    ))

    return trainer, metricas_finales, resultado


# =====================================================================
# 7. REGISTRO EN MLFLOW
# =====================================================================

def registrar_en_mlflow(trainer, tokenizer, metricas_finales, resultado_train, dataset):
    """Registra todo el experimento en MLflow (AC-11)."""
    print("\n" + "=" * 60)
    print("  FASE 5: REGISTRO EN MLFLOW (bóveda AC-11)")
    print("=" * 60)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"  🔗 Conectado a MLflow: {MLFLOW_TRACKING_URI}")

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        mlflow.create_experiment(EXPERIMENT_NAME)
        print(f"  📁 Experimento creado: {EXPERIMENT_NAME}")
    else:
        print(f"  📁 Experimento existente: {EXPERIMENT_NAME}")

    mlflow.set_experiment(EXPERIMENT_NAME)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"lora_r{LORA_CONFIG['r']}_epochs{HYPERPARAMS['num_train_epochs']}_{timestamp}"

    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        print(f"  🆔 Run ID: {run_id}")
        print(f"  📝 Run Name: {run_name}")

        # --- Parámetros ---
        print(f"\n  📌 Registrando parámetros...")
        mlflow.log_param("modelo_base", MODEL_BASE)
        mlflow.log_param("num_labels", NUM_LABELS)
        mlflow.log_param("dataset_train_size", len(dataset["train"]))
        mlflow.log_param("dataset_val_size", len(dataset["validation"]))
        mlflow.log_param("labels", json.dumps(LABEL_MAP))

        for k, v in HYPERPARAMS.items():
            mlflow.log_param(f"train_{k}", v)

        for k, v in LORA_CONFIG.items():
            if k != "task_type":
                mlflow.log_param(f"lora_{k}", str(v))

        params_total = sum(p.numel() for p in trainer.model.parameters())
        params_trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
        mlflow.log_param("params_total", params_total)
        mlflow.log_param("params_trainable", params_trainable)
        mlflow.log_param("params_trainable_pct", round(params_trainable / params_total * 100, 2))
        mlflow.log_param("device", "cuda" if torch.cuda.is_available() else "cpu")

        # --- Métricas ---
        print(f"  📈 Registrando métricas...")
        for metrica, valor in metricas_finales.items():
            if metrica.startswith("eval_"):
                nombre_limpio = metrica.replace("eval_", "")
                mlflow.log_metric(nombre_limpio, valor)
                print(f"     {nombre_limpio:<25} {valor:.4f}")

        mlflow.log_metric("train_loss_final", resultado_train.training_loss, step=resultado_train.global_step)
        if resultado_train.metrics:
            for k, v in resultado_train.metrics.items():
                mlflow.log_metric(f"train_{k}", v, step=resultado_train.global_step)

        # --- Modelo ---
        print(f"\n  💾 Guardando modelo en disco local...")
        
        # 1. Crear carpeta de almacenamiento
        storage_dir = Path("./modelos_storage")
        storage_dir.mkdir(exist_ok=True)
        modelo_dir = storage_dir / "temp_guardado"
        
        # 2. Guardar archivos del modelo
        trainer.model.save_pretrained(str(modelo_dir))
        tokenizer.save_pretrained(str(modelo_dir))
        with open(str(modelo_dir / "label_map.json"), "w") as f:
            json.dump(LABEL_MAP, f, indent=2)
            
        # 3. Comprimir y nombrar EXACTAMENTE con el Run ID de MLflow
        zip_path = storage_dir / f"{run_id}.zip"
        shutil.make_archive(
            base_name=str(zip_path.with_suffix('')), 
            format='zip', 
            base_dir=str(modelo_dir)
        )
        
        # 4. Intentar subir a MLflow (si falla el Docker, no importa)
        try:
            mlflow.log_artifact(str(zip_path), artifact_path="modelo_lora")
            print(f"     ✅ También subido a la UI de MLflow.")
        except Exception as e:
            print(f"     ⚠️  No se pudo subir a MLflow UI (usando disco local): {e}")
            
        # 5. Limpiar carpeta temporal (el ZIP se queda guardado)
        shutil.rmtree(str(modelo_dir), ignore_errors=True)

        # --- Tags ---
        print(f"  🏷️  Registrando tags...")
        mlflow.set_tag("status", "candidato")
        mlflow.set_tag("ac", "AC-06")
        mlflow.set_tag("tecnica", "LoRA")
        mlflow.set_tag("modelo_base", MODEL_BASE)
        mlflow.set_tag("fecha_entrenamiento", datetime.now().isoformat())
        mlflow.set_tag("dataset_version", timestamp)
        mlflow.set_tag("proyecto", "Sistema_Aprendizaje_Continuo")

        accuracy = metricas_finales.get("eval_accuracy", 0)
        if accuracy >= MIN_ACCURACY:
            mlflow.set_tag("cumple_umbral", "si")
            print(f"  ✅ Accuracy {accuracy:.4f} >= umbral {MIN_ACCURACY}")
        else:
            mlflow.set_tag("cumple_umbral", "no")
            print(f"  ⚠️  Accuracy {accuracy:.4f} < umbral {MIN_ACCURACY}")

        print(f"\n  {'=' * 50}")
        print(f"  ✅ EXPERIMENTO REGISTRADO EN MLFLOW")
        print(f"  {'=' * 50}")
        print(f"  🌐 URL: {MLFLOW_TRACKING_URI}/#/experiments/{EXPERIMENT_NAME}/runs/{run_id}")
        print(f"  🆔 Run ID: {run_id}")
        print(f"  🏷️  Estado: CANDIDATO (espera validación AC-08)")
        print(f"  {'=' * 50}")

    # Limpiar temporales
    # import shutil
    # if os.path.exists(modelo_dir):
    #     shutil.rmtree(modelo_dir)

    # return run_id


# =====================================================================
# 8. PRUEBA RÁPIDA DEL MODELO
# =====================================================================

def probar_modelo(trainer, tokenizer):
    """Prueba el modelo con ejemplos para verificar que funciona."""
    print("\n" + "=" * 60)
    print("  FASE 6: PRUEBA RÁPIDA DEL MODELO")
    print("=" * 60)

    clasificador = pipeline(
        "text-classification",
        model=trainer.model,
        tokenizer=tokenizer,
        top_k=None,
    )

    frases_prueba = [
        "Quiero cancelar mi servicio de internet",
        "¿Cuánto saldo me queda en mi cuenta?",
        "Necesito cambiar a un plan más económico",
        "Me cobraron dos veces este mes, quiero un reclamo",
        "La aplicación no funciona correctamente",
        "Quiero hablar con un agente humano por favor",
        "¿Qué planes tienen disponibles?",
        "Hola, buenos días",
    ]

    print(f"\n  🧪 Probando con {len(frases_prueba)} frases de ejemplo:\n")

    for frase in frases_prueba:
        resultado = clasificador(frase)[0]
        resultado_ordenado = sorted(resultado, key=lambda x: x["score"], reverse=True)
        top = resultado_ordenado[0]

        confianza_pct = top["score"] * 100
        barra_len = int(confianza_pct / 5)
        barra = "█" * barra_len + "░" * (20 - barra_len)

        print(f"  💬 \"{frase}\"")
        print(f"     → {top['label']:<25} [{barra}] {confianza_pct:.1f}%")
        print()


# =====================================================================
# 9. FUNCIÓN PRINCIPAL
# =====================================================================

def main():
    """Ejecución principal del pipeline de fine-tuning AC-06."""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║  AC-06: FINE-TUNING DEL MODELO CON LORA                ║")
    print("║  Sistema de Aprendizaje Continuo                       ║")
    print("║  PluriOne S.A. de C.V. — Develop Talent & Technology   ║")
    print("╚" + "═" * 58 + "╝")

    try:
        # FASE 1: Cargar datos
        datos_train, datos_val = cargar_datasets(DATASETS_DIR)

        # FASE 2: Crear modelo con LoRA
        modelo, tokenizer = crear_modelo_con_lora()

        # FASE 3: Preparar dataset
        dataset = preparar_dataset_hf(datos_train, datos_val, tokenizer)

        # FASE 4: Entrenar
        trainer, metricas_finales, resultado_train = entrenar_modelo(
            modelo, tokenizer, dataset
        )

        # FASE 5: Probar modelo
        probar_modelo(trainer, tokenizer)

        # FASE 6: Registrar en MLflow
        run_id = registrar_en_mlflow(
            trainer, tokenizer, metricas_finales, resultado_train, dataset
        )

        # Resumen final
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║  ✅ AC-06 COMPLETADO EXITOSAMENTE                   ║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  Modelo:     {MODEL_BASE:<37}║")
        print(f"║  Técnica:    LoRA (r={LORA_CONFIG['r']}){' ' * 27}║")
        acc = metricas_finales.get('eval_accuracy', 0)
        print(f"║  Accuracy:   {acc:.4f}{' ' * 31}║")
        f1 = metricas_finales.get('eval_f1_macro', 0)
        print(f"║  F1 Macro:   {f1:.4f}{' ' * 31}║")
        print("║  Estado:     CANDIDATO                                 ║")
        print("╠" + "═" * 58 + "╣")
        print("║  🔜 SIGUIENTE PASO: AC-08                            ║")
        print("║  Validar modelo y rollback automático                ║")
        print("╚" + "═" * 58 + "╝\n")

        return run_id

    except Exception as e:
        print(f"\n  ❌ ERROR FATAL EN AC-06: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()