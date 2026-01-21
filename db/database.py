import sqlite3

class Database:
    def __init__(self, db_path="data/database.db", schema_path="data/schema.sql") -> None:
        self.db_name = db_path
        self.schema_path = schema_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with open(self.schema_path, 'r') as f:
                schema = f.read()
            conn = self._get_connection()
            try:
                conn.executescript(schema)
                conn.commit()
            finally:
                conn.close()
        except FileNotFoundError:
            print(f"BŁĄD: Nie znaleziono pliku schematu.")

    def fetch_all(self, query, params=()):
        conn = self._get_connection()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def fetch_one(self, query, params=()):
        conn = self._get_connection()
        try:
            return conn.execute(query, params).fetchone()
        finally:
            conn.close()

    def execute(self, query, params=()):
        conn = self._get_connection()
        try:
            cur = conn.execute(query, params)
            conn.commit()
            return cur 
        finally:
            conn.close()
