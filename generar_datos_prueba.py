# generar_datos_prueba.py
"""Genera datos sintéticos para probar AC-06 mientras AC-05 produce datos reales."""
import json
import random
from pathlib import Path

INTENCIONES = {
    "consulta_saldo": [
        "¿Cuánto saldo me queda?",
        "Quiero saber mi balance",
        "Me puedes decir cuánto tengo disponible",
        "Necesito checar mi saldo pendiente",
        "¿Cómo veo mi saldo?",
    ],
    "cambio_plan": [
        "Quiero cambiar mi plan a uno superior",
        "Necesito un plan más barato",
        "Me interesa cambiar de paquete",
        "¿Puedo migrar a otro plan?",
        "Quiero actualizar mi suscripción",
    ],
    "cancelacion_servicio": [
        "Quiero cancelar mi servicio",
        "Necesito dar de baja mi cuenta",
        "Ya no quiero el servicio, cancelenlo",
        "Por favor cancelen mi suscripción",
        "Deseo terminar mi contrato",
    ],
    "reclamo_facturacion": [
        "Me cobraron dos veces este mes",
        "Tengo un cargo que no reconozco",
        "La factura está mal calculada",
        "Me cobraron algo que no compré",
        "Quiero reclamar un cargo indebido",
    ],
    "problema_tecnico": [
        "No me funciona la aplicación",
        "Se cae el servicio cada rato",
        "La página no carga",
        "Tengo problemas de conexión",
        "El sistema está muy lento",
    ],
    "solicitar_humano": [
        "Quiero hablar con una persona",
        "Pásame con un agente",
        "Necesito atención humana",
        "No quiero hablar con un bot",
        "Comuníquenme con alguien",
    ],
    "info_productos": [
        "¿Qué planes tienen disponibles?",
        "Quiero conocer sus servicios",
        "¿Cuáles son los precios?",
        "Necesito información sobre los paquetes",
        "¿Qué ofrecen nuevo?",
    ],
    "otro": [
        "Buenos días",
        "Gracias por la ayuda",
        "Hola",
        "Ok, entendido",
        "Nada más por ahora",
    ],
}

def generar_dataset(num_muestras=300, ruta_salida="datasets_ac05"):
    Path(ruta_salida).mkdir(exist_ok=True)
    datos = []

    for _ in range(num_muestras):
        intencion = random.choice(list(INTENCIONES.keys()))
        texto = random.choice(INTENCIONES[intencion])
        # Agregar variación aleatoria
        variaciones = [
            texto,
            texto.lower(),
            texto + ".",
            "Oye, " + texto.lower(),
            texto + " por favor",
        ]
        datos.append({
            "texto_usuario": random.choice(variaciones),
            "intencion": intencion,
        })

    random.shuffle(datos)

    # Separar: 80% entrenamiento, 20% validación
    split = int(len(datos) * 0.8)
    train = datos[:split]
    val = datos[split:]

    with open(f"{ruta_salida}/train_intenciones.jsonl", "w", encoding="utf-8") as f:
        for d in train:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    with open(f"{ruta_salida}/val_intenciones.jsonl", "w", encoding="utf-8") as f:
        for d in val:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print(f"✅ Generados: {len(train)} train + {len(val)} val = {len(datos)} total")
    print(f"   Guardados en: {ruta_salida}/")

if __name__ == "__main__":
    generar_dataset(500)