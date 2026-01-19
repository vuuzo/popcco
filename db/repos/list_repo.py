class ListRepo:
    def __init__(self, db) -> None:
        self.db = db

    def create_list(self, user_id: int, name: str, description: str = ""):
        """Tworzy nową, pustą listę użytkownika."""
        self.db.execute(
            "INSERT INTO lists (user_id, name, description) VALUES (?, ?, ?)",
            (user_id, name, description)
        )

    def get_user_lists(self, user_id: int):
        """Pobiera wszystkie listy stworzone przez użytkownika."""
        return self.db.fetch_all(
            "SELECT id, name, created_at FROM lists WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

    def get_list_details(self, list_id: int, user_id: int):
        """Pobiera dane o liście (nazwę), sprawdzając czy należy do użytkownika."""
        return self.db.fetch_one(
            "SELECT id, name FROM lists WHERE id = ? AND user_id = ?", 
            (list_id, user_id)
        )

    def remove_movie(self, list_id: int, movie_id: int):
        query = """DELETE FROM list_movies WHERE list_id = ? AND tmdb_id = ?;"""
        self.db.execute(query, (list_id, movie_id))

    def get_list(self, list_id: int):
        """Pobiera dane o liście."""
        return self.db.fetch_one(
            "SELECT * FROM lists WHERE id = ?", 
            (list_id, )
        )

    def get_all_lists(self):
        """Pobiera wszystkie listy wraz z maksymalnie 3 plakatami filmów dla każdej."""
        sql = """
            SELECT 
                l.id, l.name, l.created_at, u.username,
                (SELECT GROUP_CONCAT(poster_path) FROM (
                    SELECT mc.poster_path 
                    FROM list_movies lm
                    JOIN movies_cache mc ON lm.tmdb_id = mc.tmdb_id
                    WHERE lm.list_id = l.id
                    ORDER BY lm.created_at DESC
                    LIMIT 3
                )) as posters
            FROM lists l
            JOIN users u ON l.user_id = u.id
            WHERE EXISTS (
                SELECT 1 FROM list_movies lm WHERE lm.list_id = l.id
            )
            ORDER BY l.created_at DESC
        """
        rows = self.db.fetch_all(sql)
        
        results = []
        for row in rows:
            # Zamiana row na słownik
            list_dict = dict(row)
            if list_dict['posters']:
                list_dict['posters'] = list_dict['posters'].split(',')
            else:
                list_dict['posters'] = []
            results.append(list_dict)
            
        return results

    def add_movie_to_list(self, list_id: int, user_id: int, tmdb_id: int):
        """
        Dodaje film do listy tylko wtedy, gdy lista należy do danego użytkownika.
        """
        self.db.execute("""
            INSERT OR IGNORE INTO list_movies (list_id, tmdb_id, created_at)
            SELECT id, ?, CURRENT_TIMESTAMP FROM lists 
            WHERE id = ? AND user_id = ?
        """, (tmdb_id, list_id, user_id))

    def get_list_movies(self, list_id: int):
        """Pobiera wszystkie filmy przypisane do danej listy."""
        return self.db.fetch_all("""
            SELECT lm.tmdb_id, mc.title, mc.poster_path
            FROM list_movies lm
            JOIN movies_cache mc ON lm.tmdb_id = mc.tmdb_id
            WHERE lm.list_id = ?
            ORDER BY lm.created_at DESC
        """, (list_id,))

    def delete_list(self, list_id: int, user_id: int):
        """Usuwa listę (jeśli należy do użytkownika)."""
        self.db.execute("DELETE FROM list_movies WHERE list_id = ?", (list_id,))
        self.db.execute("DELETE FROM lists WHERE id = ? AND user_id = ?", (list_id, user_id))
