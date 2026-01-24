import sqlite3
from flask import g, current_app

class Database:
    def __init__(self, app=None) -> None:
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Rejestruje funkcję zamykania bazy w aplikacji Flask"""
        # Ta metoda mówi Flaskowi: "jak skończysz obsługiwać żądanie, wywołaj close_db"
        app.teardown_appcontext(self.close_db)

    def get_db(self):
        """Zwraca połączenie z bazy. Jeśli nie ma w 'g', tworzy je."""
        if 'db' not in g:
            g.db = sqlite3.connect("data/database.db")
            g.db.row_factory = sqlite3.Row
            # włączenie Foreign Keys
            g.db.execute("PRAGMA foreign_keys = ON")
        
        return g.db

    def close_db(self, e=None):
        """Zamyka połączenie, jeśli istnieje w 'g'."""
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def fetch_all(self, query, params=()):
        db = self.get_db()
        cursor = db.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        db = self.get_db()
        cursor = db.execute(query, params)
        return cursor.fetchone()

    def execute(self, query, params=()):
        db = self.get_db()
        cursor = db.execute(query, params)
        db.commit()
        return cursor

# import sqlite3
#
# class Database:
#     def __init__(self, db_path="data/database.db", schema_path="data/schema.sql") -> None:
#         self.db_name = db_path
#         self.schema_path = schema_path
#         self._init_db()
#
#     def _get_connection(self):
#         conn = sqlite3.connect(self.db_name)
#         conn.row_factory = sqlite3.Row
#         return conn
#
#     def _init_db(self):
#         try:
#             with open(self.schema_path, 'r') as f:
#                 schema = f.read()
#             conn = self._get_connection()
#             try:
#                 conn.executescript(schema)
#                 conn.commit()
#             finally:
#                 conn.close()
#         except FileNotFoundError:
#             print(f"BŁĄD: Nie znaleziono pliku schematu.")
#
#     def fetch_all(self, query, params=()):
#         conn = self._get_connection()
#         try:
#             return conn.execute(query, params).fetchall()
#         finally:
#             conn.close()
#
#     def fetch_one(self, query, params=()):
#         conn = self._get_connection()
#         try:
#             return conn.execute(query, params).fetchone()
#         finally:
#             conn.close()
#
#     def execute(self, query, params=()):
#         conn = self._get_connection()
#         try:
#             cur = conn.execute(query, params)
#             conn.commit()
#             return cur 
#         finally:
#             conn.close()
