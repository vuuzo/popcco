import sqlite3
from flask import g

class Database:
    def __init__(self, app=None) -> None:
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Rejestruje funkcję zamykania bazy (Flask)"""
        app.teardown_appcontext(self.close_db)

    def get_db(self):
        """Zwraca połączenie z bazy"""
        if 'db' not in g:
            g.db = sqlite3.connect("data/database.db")
            g.db.row_factory = sqlite3.Row
            # włączenie FK
            g.db.execute("PRAGMA foreign_keys = ON")
        
        return g.db

    def close_db(self, e=None):
        """Zamyka połączenie"""
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

