import psycopg2

def conectar_db():
    return psycopg2.connect(
        host="localhost",
        database="aprendizaje_db",
        user="usuario_learning",
        password="password_secreto",
        port="5432"
    )

def correr_migracion():
    print("🔧 Iniciando migración de base de datos para AC-05...\n")
    
    conn = conectar_db()
    cursor = conn.cursor()

    migraciones = [
        # Texto que escribió el usuario en la interacción
        """
        ALTER TABLE logs_interacciones
        ADD COLUMN IF NOT EXISTS texto_usuario TEXT;
        """,
        # Respuesta que dio el bot / resolutor
        """
        ALTER TABLE logs_interacciones
        ADD COLUMN IF NOT EXISTS respuesta_agente TEXT;
        """,
        # Corrección esperada (se llena manualmente o con lógica para datos FALLIDO)
        """
        ALTER TABLE logs_interacciones
        ADD COLUMN IF NOT EXISTS correccion_esperada TEXT;
        """,
        # Clasificación del punto de ruptura (ya la calculas, ahora la guardamos)
        """
        ALTER TABLE logs_interacciones
        ADD COLUMN IF NOT EXISTS clasificacion_error VARCHAR(100);
        """,
        # Marca si este registro ya fue incluido en un dataset curado
        """
        ALTER TABLE logs_interacciones
        ADD COLUMN IF NOT EXISTS incluido_en_dataset BOOLEAN DEFAULT FALSE;
        """,
    ]

    for i, sql in enumerate(migraciones, 1):
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"  ✅ Migración {i}/5 completada.")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️  Migración {i}/5 ya existía o falló: {e}")

    # Verificar resultado final
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'logs_interacciones'
        ORDER BY ordinal_position;
    """)
    columnas = cursor.fetchall()

    print("\n📋 Estructura final de logs_interacciones:")
    for col in columnas:
        print(f"   - {col[0]:30s} {col[1]}")

    cursor.close()
    conn.close()
    print("\n✅ Migración completada. Ya puedes correr el consumidor actualizado.")

if __name__ == "__main__":
    correr_migracion()