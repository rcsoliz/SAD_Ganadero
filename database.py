import psycopg2
import pandas as pd

# Tu cadena URI del Pooler de Supabase (Mantenla tal como la tenías)
DB_URI = "postgresql://postgres.ahplhuivlpgjahkzyayx:1Tarechi$$2026@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"

def obtener_conexion():
    return psycopg2.connect(DB_URI)

def inicializar_base_datos_si_no_existe():
    """Crea la tabla adaptada a multi-usuario e inyecta datos de prueba si está vacía."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # NUEVO: Añadimos la columna 'usuario' para separar los datos de las estancias
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS potreros (
        id SERIAL PRIMARY KEY,
        usuario VARCHAR(50) NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        hectareas REAL NOT NULL,
        dias_descanso INTEGER NOT NULL
    );
    ''')
    conn.commit()
    
    # Comprobar si está vacía
    cursor.execute("SELECT COUNT(*) FROM potreros;")
    if cursor.fetchone()[0] == 0:
        # Inyectamos datos para dos usuarios diferentes para probar el aislamiento de seguridad
        datos_iniciales = [
            # Datos para el usuario 'roberto'
            ("roberto", "Potrero 1 (La Loma)", 40.0, 55),
            ("roberto", "Potrero 2 (El Bajío)", 35.0, 20),
            ("roberto", "Potrero 3 (El Tajibo)", 50.0, 40),
            # Datos para otro usuario de prueba 'ganadero2'
            ("ganadero2", "Potrero Norte A", 120.0, 15),
            ("ganadero2", "Potrero Norte B", 80.0, 65)
        ]
        cursor.executemany(
            'INSERT INTO potreros (usuario, nombre, hectareas, dias_descanso) VALUES (%s, %s, %s, %s)', 
            datos_iniciales
        )
        conn.commit()
        
    cursor.close()
    conn.close()

def cargar_datos_desde_db(usuario_actual):
    """NUEVO: Recupera ÚNICAMENTE los potreros del usuario que inició sesión."""
    inicializar_base_datos_si_no_existe()
    conn = obtener_conexion()
    
    # Clausula WHERE indispensable para la seguridad multi-usuario
    query = """
        SELECT id AS "ID", 
               nombre AS "Potrero", 
               hectareas AS "Hectáreas", 
               dias_descanso AS "Días de Descanso" 
        FROM potreros 
        WHERE usuario = %s 
        ORDER BY id ASC
    """
    
    # Pasamos el usuario como parámetro seguro para evitar SQL Injection
    df = pd.read_sql_query(query, conn, params=(usuario_actual,))
    conn.close()
    return df

def insertar_potrero(usuario_actual, nombre, ha, dias):
    """NUEVO: Guarda el potrero asociándolo al usuario activo."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO potreros (usuario, nombre, hectareas, dias_descanso) VALUES (%s, %s, %s, %s)", 
        (usuario_actual, nombre, ha, dias)
    )
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_potrero_especifico(id_potrero, nuevos_dias):
    """Este se mantiene igual ya que el ID es único globalmente."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE potreros SET dias_descanso = %s WHERE id = %s", (nuevos_dias, id_potrero))
    conn.commit()
    cursor.close()
    conn.close()