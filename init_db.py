import sqlite3
import os

db_path = "data/database.db"
schema_path = "data/schema.sql"

if not os.path.exists(schema_path):
    print(f"Błąd: Nie znaleziono pliku schematu w {schema_path}")
    exit(1)

connection = sqlite3.connect(db_path)

with open(schema_path, 'r', encoding='utf-8') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Baza danych została pomyślnie zainicjowana!")
