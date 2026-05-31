import psycopg2
import pandas as pd

# Tu cadena URI de Supabase
DB_URI = "postgresql://postgres.ahplhuivlpgjahkzyayx:1Tarechi$$2026@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

def obtener_conexion():
    return psycopg2.connect(DB_URI)

def inicializar_base_datos_si_no_existe():
    """Crea la tabla adaptada a telemetria satelital (NDVI)."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # NUEVO: Añadimos 'coordenadas' y el valor 'ndvi' (por defecto 0.3)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS potreros (
        id SERIAL PRIMARY KEY,
        usuario VARCHAR(50) NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        hectareas REAL NOT NULL,
        dias_descanso INTEGER NOT NULL,
        coordenadas VARCHAR(100) DEFAULT '-17.8, -63.1',
        ndvi REAL DEFAULT 0.3
    );
    ''')
    conn.commit()
    
    # Comprobar si está vacía
    cursor.execute("SELECT COUNT(*) FROM potreros;")
    if cursor.fetchone()[0] == 0:
        datos_iniciales = [
            ("roberto", "Potrero 1 (La Loma)", 40.0, 55, "-17.312, -63.221", 0.72),
            ("roberto", "Potrero 2 (El Bajío)", 35.0, 20, "-17.315, -63.225", 0.35),
            ("roberto", "Potrero 3 (El Tajibo)", 50.0, 40, "-17.318, -63.230", 0.61),
            ("ganadero2", "Potrero Norte A", 120.0, 15, "-16.120, -62.310", 0.21),
            ("ganadero2", "Potrero Norte B", 80.0, 65, "-16.125, -62.315", 0.78)
        ]
        cursor.executemany(
            'INSERT INTO potreros (usuario, nombre, hectareas, dias_descanso, coordenadas, ndvi) VALUES (%s, %s, %s, %s, %s, %s)', 
            datos_iniciales
        )
        conn.commit()
        
    cursor.close()
    conn.close()

def cargar_datos_desde_db(usuario_actual):
    """Recupera los potreros incluyendo el NDVI satelital."""
    inicializar_base_datos_si_no_existe()
    conn = obtener_conexion()
    
    query = """
        SELECT id AS "ID", 
               nombre AS "Potrero", 
               hectareas AS "Hectáreas", 
               dias_descanso AS "Días de Descanso",
               coordenadas AS "Coordenadas GPS",
               ndvi AS "Índice NDVI Satelital"
        FROM potreros 
        WHERE usuario = %s 
        ORDER BY id ASC
    """
    df = pd.read_sql_query(query, conn, params=(usuario_actual,))
    conn.close()
    return df

def insertar_potrero(usuario_actual, nombre, ha, dias, coordenadas="-17.8, -63.1"):
    """Permite guardar un potrero incluyendo sus coordenadas."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO potreros (usuario, nombre, hectareas, dias_descanso, coordenadas, ndvi) VALUES (%s, %s, %s, %s, %s, 0.35)", 
        (usuario_actual, nombre, ha, dias, coordenadas)
    )
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

def simular_actualizacion_satelital_global(id_potrero, nuevo_ndvi):
    """Función que usará el script remoto para inyectar telemetría en tiempo real."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE potreros SET ndvi = %s WHERE id = %s", (nuevo_ndvi, id_potrero))
    conn.commit()
    cursor.close()
    conn.close()