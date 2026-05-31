import psycopg2
import pandas as pd

# ⚠️ REEMPLAZA ESTO CON TU CADENA URI REAL DE SUPABASE
# Recuerda colocar tu contraseña real en lugar de [your-password]
DB_URI = "postgresql://postgres:1Tarechi$$2026@db.ahplhuivlpgjahkzyayx.supabase.co:5432/postgres"

def obtener_conexion():
    """Establece una conexión segura con la base de datos PostgreSQL en Supabase."""
    return psycopg2.connect(DB_URI)

def inicializar_base_datos_si_no_existe():
    """Crea la tabla en Supabase si no existe y le inyecta los datos iniciales cruceños."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # En Postgres usamos VARCHAR en lugar de TEXT, y SERIAL en lugar de AUTOINCREMENT
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS potreros (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        hectareas REAL NOT NULL,
        dias_descanso INTEGER NOT NULL
    );
    ''')
    conn.commit()
    
    # Comprobar si la tabla ya tiene registros para no duplicar datos
    cursor.execute("SELECT COUNT(*) FROM potreros;")
    if cursor.fetchone()[0] == 0:
        datos_iniciales = [
            ("Potrero 1 (La Loma)", 40.0, 55),
            ("Potrero 2 (El Bajío)", 35.0, 20),
            ("Potrero 3 (El Tajibo)", 50.0, 40),
            ("Potrero 4 (Las Curichi)", 60.0, 15),
            ("Potrero 5 (El Totai)", 45.0, 70)
        ]
        # En Postgres los marcadores de posición son %s en lugar de ?
        cursor.executemany('INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (%s, %s, %s)', datos_iniciales)
        conn.commit()
        
    cursor.close()
    conn.close()

def cargar_datos_desde_db():
    """Asegura la inicialización y recupera los datos desde Supabase."""
    inicializar_base_datos_si_no_existe()
    conn = obtener_conexion()
    query = "SELECT id AS \"ID\", nombre AS \"Potrero\", hectareas AS \"Hectáreas\", dias_descanso AS \"Días de Descanso\" FROM potreros ORDER BY id ASC"
    
    # Pandas procesa la query SQL directamente desde la conexión remota
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def insertar_potrero(nombre, ha, dias):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (%s, %s, %s)", (nombre, ha, dias))
    conn.commit()
    cursor.close()
    conn.close()

def actualizar_potrero_especifico(id_potrero, nuevos_dias):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE potreros SET dias_descanso = %s WHERE id = %s", (nuevos_dias, id_potrero))
    conn.commit()
    cursor.close()
    conn.close()