import sqlite3
import pandas as pd
import os

DB_NAME = 'ganaderia.db'

def obtener_conexion():
    """Establece y retorna una conexión a la base de datos."""
    return sqlite3.connect(DB_NAME)

def inicializar_base_datos_si_no_existe():
    """Verifica si el archivo .db existe en el servidor. Si no, lo crea y lo puebla."""
    if not os.path.exists(DB_NAME):
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # Crear Tabla
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS potreros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            hectareas REAL NOT NULL,
            dias_descanso INTEGER NOT NULL
        )
        ''')
        
        # Insertar datos ficticios iniciales de Santa Cruz
        datos_iniciales = [
            ("Potrero 1 (La Loma)", 40.0, 55),
            ("Potrero 2 (El Bajío)", 35.0, 20),
            ("Potrero 3 (El Tajibo)", 50.0, 40),
            ("Potrero 4 (Las Curichi)", 60.0, 15),
            ("Potrero 5 (El Totai)", 45.0, 70)
        ]
        cursor.executemany('INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (?, ?, ?)', datos_iniciales)
        conn.commit()
        conn.close()

def cargar_datos_desde_db():
    """Asegura que la DB exista y recupera los datos."""
    inicializar_base_datos_si_no_existe() # <-- Lógica inteligente para la nube
    conn = obtener_conexion()
    query = """
        SELECT id AS ID, 
               nombre AS Potrero, 
               hectareas AS Hectáreas, 
               dias_descanso AS [Días de Descanso] 
        FROM potreros
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def insertar_potrero(nombre, ha, dias):
    inicializar_base_datos_si_no_existe()
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (?, ?, ?)", (nombre, ha, dias))
    conn.commit()
    conn.close()

def actualizar_potrero_especifico(id_potrero, nuevos_dias):
    inicializar_base_datos_si_no_existe()
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE potreros SET dias_descanso = ? WHERE id = ?", (nuevos_dias, id_potrero))
    conn.commit()
    conn.close()