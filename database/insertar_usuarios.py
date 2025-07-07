import sqlite3

conn = sqlite3.connect('database/estacionamiento.db')
cursor = conn.cursor()

# Asegura que la tabla exista
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        patente TEXT PRIMARY KEY,
        tipo TEXT NOT NULL CHECK(tipo IN ('Estudiante', 'Profesor')),
        activo INTEGER NOT NULL DEFAULT 1
    )
''')

usuarios = [
    ("VT4909", "Profesor"),
    ("FFFG19", "Estudiante"),
    ("HWWG94", "Estudiante"),
    ("RZGG39", "Profesor"),
    ("DHKD30", "Estudiante"),
    ("PHTJ34", "Estudiante"),
    ("GFDP80", "Profesor"),
    ("BBXR64", "Estudiante"),
]

for patente, tipo in usuarios:
    try:
        cursor.execute("INSERT INTO usuarios (patente, tipo) VALUES (?, ?)", (patente.upper(), tipo))
    except sqlite3.IntegrityError:
        print(f"Ya existe: {patente}")

conn.commit()
conn.close()
