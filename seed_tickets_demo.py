"""
seed_tickets_demo.py — Inserta ~35 tickets sintéticos en tickets_clasificados.

Uso:
  python seed_tickets_demo.py           → inserta 35 tickets demo
  python seed_tickets_demo.py --reset   → borra SOLO los demo (texto LIKE '[DEMO]%')

Los tickets reales (sin prefijo [DEMO]) nunca se tocan.
"""

import argparse
import uuid
import sys
from datetime import datetime, timedelta

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")
    sys.exit(1)

DB = dict(
    host="localhost",
    port=5432,
    dbname="aprendizaje_db",
    user="usuario_learning",
    password="password_secreto",
)

# (categoria, prioridad, texto, confianza, dias_atras, estado)
TICKETS = [
    ("facturacion",         "alta",  "Me cobraron dos veces el mismo mes",                               0.92, 1,  "abierto"),
    ("facturacion",         "alta",  "Mi factura no coincide con el servicio contratado",                0.88, 3,  "abierto"),
    ("facturacion",         "alta",  "Hay un cargo desconocido en mi estado de cuenta",                  0.85, 5,  "abierto"),
    ("facturacion",         "alta",  "No he recibido la factura de este mes",                            0.81, 7,  "cerrado"),
    ("facturacion",         "alta",  "El monto debitado fue mayor al acordado",                          0.90, 10, "abierto"),

    ("tarjeta_bancaria",    "alta",  "Perdí mi tarjeta y necesito bloquearla urgente",                   0.94, 0,  "abierto"),
    ("tarjeta_bancaria",    "alta",  "Mi tarjeta fue clonada, hubo cargos que no hice",                  0.91, 2,  "abierto"),
    ("tarjeta_bancaria",    "alta",  "La tarjeta fue rechazada en un establecimiento",                   0.78, 4,  "abierto"),
    ("tarjeta_bancaria",    "alta",  "Quiero solicitar una nueva tarjeta de débito",                     0.72, 8,  "cerrado"),
    ("tarjeta_bancaria",    "alta",  "No puedo activar mi tarjeta nueva",                                0.83, 12, "abierto"),

    ("queja_general",       "alta",  "El servicio al cliente tardó 3 días en responder",                 0.76, 1,  "abierto"),
    ("queja_general",       "alta",  "Recibí un trato muy grosero del agente",                           0.80, 6,  "abierto"),
    ("queja_general",       "alta",  "Prometieron resolver mi caso y nadie me contactó",                 0.74, 9,  "abierto"),
    ("queja_general",       "alta",  "Estoy muy insatisfecho con la resolución de mi queja",             0.69, 13, "cerrado"),

    ("soporte_tecnico",     "media", "La aplicación se cierra sola al abrir el historial",               0.86, 1,  "abierto"),
    ("soporte_tecnico",     "media", "No puedo hacer pagos desde la app en iOS",                         0.82, 3,  "abierto"),
    ("soporte_tecnico",     "media", "La pantalla de confirmación queda en blanco",                      0.79, 5,  "abierto"),
    ("soporte_tecnico",     "media", "El módulo de reportes no carga nada",                              0.70, 7,  "cerrado"),
    ("soporte_tecnico",     "media", "La notificación push no llega aunque esté activada",               0.65, 11, "abierto"),

    ("cuenta_acceso",       "media", "Olvidé mi contraseña y no me llega el correo de recuperación",     0.88, 0,  "abierto"),
    ("cuenta_acceso",       "media", "Mi cuenta fue bloqueada sin motivo aparente",                      0.84, 4,  "abierto"),
    ("cuenta_acceso",       "media", "No puedo iniciar sesión desde el nuevo dispositivo",               0.77, 8,  "cerrado"),
    ("cuenta_acceso",       "media", "Quiero cambiar el correo electrónico asociado",                    0.60, 12, "abierto"),

    ("estado_pedido",       "media", "Mi pedido lleva 5 días en 'en camino' sin actualizarse",           0.83, 2,  "abierto"),
    ("estado_pedido",       "media", "Recibí solo parte del pedido, falta un artículo",                  0.79, 6,  "abierto"),
    ("estado_pedido",       "media", "El número de rastreo no existe en el sistema de paquetería",       0.73, 9,  "cerrado"),
    ("estado_pedido",       "media", "Mi pedido fue entregado a una dirección incorrecta",               0.87, 13, "abierto"),

    ("informacion_general", "baja",  "¿Cuáles son los horarios de atención al cliente?",                0.91, 1,  "cerrado"),
    ("informacion_general", "baja",  "¿Qué documentos necesito para abrir una cuenta?",                 0.88, 5,  "cerrado"),
    ("informacion_general", "baja",  "¿Tienen sucursales en Monterrey?",                                0.85, 9,  "abierto"),
    ("informacion_general", "baja",  "¿Cómo puedo solicitar un estado de cuenta en PDF?",               0.79, 13, "abierto"),

    ("otros",               "baja",  "Quisiera que añadieran modo oscuro a la app",                     0.55, 2,  "cerrado"),
    ("otros",               "baja",  "Me gustaría recibir recordatorios de pago por WhatsApp",          0.52, 7,  "cerrado"),
    ("otros",               "baja",  "¿Tienen programa de puntos o recompensas?",                       0.61, 10, "abierto"),
    ("otros",               "baja",  "Felicitaciones, el nuevo diseño de la app es muy bueno",          0.48, 14, "abierto"),
]


def conectar():
    try:
        return psycopg2.connect(**DB)
    except psycopg2.OperationalError as e:
        print(f"ERROR: No se pudo conectar a PostgreSQL.\n  {e}")
        print("  Verifica que Docker esté corriendo y el contenedor de PG esté activo.")
        sys.exit(1)


def reset(conn):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tickets_clasificados WHERE texto LIKE '[DEMO]%'")
        n = cur.rowcount
    conn.commit()
    print(f"Eliminados {n} registros demo.")


def insertar(conn):
    now = datetime.now()
    sql = """
        INSERT INTO tickets_clasificados (id, texto, categoria, confianza, prioridad, estado, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """
    insertados = 0
    with conn.cursor() as cur:
        for i, (categoria, prioridad, texto, confianza, dias_atras, estado) in enumerate(TICKETS):
            ticket_id  = str(uuid.uuid4())
            texto_demo = f"[DEMO] {texto}"
            created_at = now - timedelta(days=dias_atras, hours=i % 10, minutes=(i * 7) % 60)
            cur.execute(sql, (ticket_id, texto_demo, categoria, confianza, prioridad, estado, created_at))
            insertados += cur.rowcount
    conn.commit()
    print(f"Insertados {insertados} tickets demo.")
    if insertados < len(TICKETS):
        omitidos = len(TICKETS) - insertados
        print(f"  ({omitidos} omitidos por conflicto — ya existían)")


def main():
    parser = argparse.ArgumentParser(description="Seed de tickets demo para el dashboard de métricas.")
    parser.add_argument("--reset", action="store_true", help="Eliminar SOLO los tickets demo (texto LIKE '[DEMO]%%')")
    args = parser.parse_args()

    conn = conectar()
    try:
        if args.reset:
            reset(conn)
        else:
            insertar(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
