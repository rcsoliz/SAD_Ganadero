import sqlite3
import pandas as pd

DB_NAME = 'ganaderia.db'

def obtener_conexion():
    """Establece y retorna una conexion a la base de datos."""
    return sqlite3.connect(DB_NAME)

def cargar_datos_desde_db():
    """Recupera todos los potreros de la base de datos y los devuelve como un DataFrame."""
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
    """Inserta un nuevo registro de potrero en la base de datos."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (?, ?, ?)", 
        (nombre, ha, dias)
    )
    conn.commit()
    conn.close()

def actualizar_potrero_especifico(id_potrero, nuevos_dias):
    """Actualiza los dias de descanso de un potrero especifico por su ID."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE potreros SET dias_descanso = ? WHERE id = ?", 
        (nuevos_dias, id_potrero)
    )
    conn.commit()
    conn.close()