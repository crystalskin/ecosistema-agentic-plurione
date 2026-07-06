# generar_datos_prueba.py
"""Genera datos sintéticos para probar AC-06 mientras AC-05 produce datos reales."""
import json
import random
from pathlib import Path

INTENCIONES = {
    "queja_cobro_duplicado": [
        "me cobraron dos veces este mes",
        "aparece un cargo duplicado en mi estado de cuenta",
        "me hicieron un doble cobro",
        "tengo dos cargos iguales en mi tarjeta",
        "me descontaron dos veces la misma cantidad",
        "cobro doble sin autorización",
        "me facturaron dos veces en el mismo periodo",
        "hay un cargo repetido que no autoricé",
        "aparecen dos pagos iguales y solo hice uno",
        "me cobraron algo que no pedí",
    ],
    "problema_tarjeta_bancaria": [
        "mi tarjeta no funciona",
        "me bloquearon la tarjeta",
        "no puedo usar mi tarjeta para pagar",
        "la tarjeta fue rechazada en el comercio",
        "quiero reportar mi tarjeta como robada",
        "no puedo activar mi tarjeta",
        "la tarjeta está bloqueada y no sé por qué",
        "me clonaron la tarjeta",
        "mi tarjeta venció y no me han enviado la nueva",
        "el terminal no lee mi tarjeta",
    ],
    "fallo_tecnico": [
        "la app no carga",
        "el sistema está caído",
        "no puedo entrar a mi cuenta",
        "la página no funciona",
        "me sale error al iniciar sesión",
        "la aplicación se cierra sola",
        "tengo problemas con la plataforma",
        "el servicio está muy lento",
        "no me deja hacer el pago en línea",
        "pantalla en blanco al abrir la app",
    ],
    "solicitud_reembolso": [
        "quiero un reembolso",
        "solicito la devolución del pago",
        "cuándo me devuelven mi dinero",
        "no me ha llegado mi reembolso",
        "cómo proceso una devolución",
        "cuánto tarda en aplicarse el reembolso",
        "quiero saber el estatus de mi devolución",
        "necesito que me abonen el reembolso pendiente",
        "a qué número llamo para pedir reembolso",
    ],
    "consulta_estado_orden": [
        "dónde está mi pedido",
        "cuándo llega mi orden",
        "quiero saber el estatus de mi compra",
        "no me ha llegado lo que pedí",
        "quiero rastrear mi paquete",
        "mi pedido dice entregado pero no lo recibí",
        "qué pasó con mi envío",
        "cuándo me entregan mi producto",
        "el seguimiento no actualiza",
        "necesito información sobre mi orden",
    ],
    "consulta_horario": [
        "a qué hora abren",
        "cuál es su horario de atención",
        "hasta qué hora atienden",
        "están abiertos los domingos",
        "cuál es el horario de la sucursal",
        "a qué hora cierran",
        "qué días tienen servicio",
        "atienden en días festivos",
        "cuándo puedo ir a la oficina",
        "tienen horario extendido",
    ],
    "consulta_direccion": [
        "dónde están ubicados",
        "cuál es la dirección",
        "cómo llego a sus oficinas",
        "en qué colonia están",
        "me dan la dirección exacta",
        "busco la sucursal más cercana",
        "cómo llegar desde el metro",
        "tienen oficina en la Ciudad de México",
        "cuál es la ubicación de la oficina",
        "me pasan la dirección por favor",
    ],
    "saludo": [
        "hola",
        "buenos días",
        "buenas tardes",
        "buen día",
        "hola me pueden ayudar",
        "hey buenas",
        "qué tal",
        "hola buen día",
        "buenas noches",
        "hola necesito ayuda",
    ],
    "despedida": [
        "gracias hasta luego",
        "adiós",
        "muchas gracias por su ayuda",
        "ya con eso me queda claro gracias",
        "bye",
        "chao",
        "hasta pronto",
        "nos vemos",
        "gracias que tenga buen día",
        "listo eso era todo gracias",
    ],
    "informacion_general": [
        "qué servicios ofrecen",
        "dan capacitación en inteligencia artificial",
        "qué cursos tienen disponibles",
        "ofrecen desarrollo de software",
        "las capacitaciones tienen costo",
        "cómo es la consultoría que manejan",
        "qué áreas de capacitación tienen",
        "dan cursos de Scrum",
        "ofrecen servicios de talento tecnológico",
        "tienen cursos de Java o programación",
    ],
}

def generar_dataset(num_muestras=500, ruta_salida="datasets_bart10"):
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