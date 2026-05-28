import sqlite3
# 1. Conectar a la base de datos (se creará el archivo ganaderia.db automáticamente)
conn = sqlite3.connect('ganaderia.db')
cursor = conn.cursor()

# 2. Crear Tabla de Potreros
cursor.execute('''
CREATE TABLE IF NOT EXISTS potreros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    hectareas REAL NOT NULL,
    dias_descanso INTEGER NOT NULL
)
''')

# 3. Limpiar datos viejos por si acaso corres el script varias veces
cursor.execute('DELETE FROM potreros')

# 4. Insertar datos ficticios iniciales (Data Seeding)
# Simulamos una estancia real con 5 potreros en diferentes etapas
datos_iniciales = [
    ("Potrero 1 (La Loma)", 40.0, 55),
    ("Potrero 2 (El Bajío)", 35.0, 20),
    ("Potrero 3 (El Tajibo)", 50.0, 40),
    ("Potrero 4 (Las Curichi)", 60.0, 15),
    ("Potrero 5 (El Totai)", 45.0, 70)
]

cursor.executemany('INSERT INTO potreros (nombre, hectareas, dias_descanso) VALUES (?, ?, ?)', datos_iniciales)

# 5. Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("¡Base de datos 'ganaderia.db' creada y poblada con éxito!")