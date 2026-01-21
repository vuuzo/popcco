from models.movie import Movie


class MovieUserData:
    def __init__(self, db) -> None:
        self.db = db

    def get_movie_from_cache(self, tmdb_id: int):
        """Zwraca dane z cache jeśli istnieją, w przeciwnym razie None."""
        return self.db.fetch_one(
            "SELECT title, poster_path FROM movies_cache WHERE tmdb_id = ?", 
            (tmdb_id,)
        )

    def _update_cache(self, tmdb_id: int, title: str, poster_path: str):
        """Metoda pomocnicza - upewnia się, że film jest w cache przed dodaniem relacji."""
        self.db.execute(
            """
            INSERT INTO movies_cache (tmdb_id, title, poster_path)
            VALUES (?, ?, ?)
            ON CONFLICT(tmdb_id) DO UPDATE SET
                title = excluded.title,
                poster_path = excluded.poster_path,
                last_updated = CURRENT_TIMESTAMP
            """,
            (tmdb_id, title, poster_path)
        )

    def add_to_watched(self, user_id: int, tmdb_id: int, rating: int | None = None):
        """Zapisuje do obejrzanych. Jeśli już istnieje, aktualizuje tylko ocenę."""
        self.db.execute("""
            INSERT INTO movies (user_id, tmdb_id, rating) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, tmdb_id) DO UPDATE SET
                rating = excluded.rating
        """, (user_id, tmdb_id, rating))

    def add_comment(self, user_id: int, tmdb_id: int, content: str):
        """Dodaje komentarz lub aktualizuje istniejący, odświeżając datę edycji."""
        self.db.execute("""
            INSERT INTO comments (user_id, tmdb_id, content, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, tmdb_id) DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, tmdb_id, content))

    def remove_comment(self, user_id: int, tmdb_id: int):
        """Usuwa komentarz podanego użytkownika pod filmem."""
        self.db.execute(
        "DELETE FROM comments WHERE user_id = ? AND tmdb_id = ?",
        (user_id, tmdb_id)
        )

    def get_all_comments(self, tmdb_id: int):
        """Pobiera komentarze wraz z nazwami użytkowników i ich ocenami filmu."""
        return self.db.fetch_all("""
            SELECT 
                c.content, 
                c.created_at, 
                c.updated_at, 
                u.username,
                m.rating
            FROM comments c
            JOIN users u ON c.user_id = u.id
            LEFT JOIN movies m ON c.user_id = m.user_id AND c.tmdb_id = m.tmdb_id
            WHERE c.tmdb_id = ?
            ORDER BY c.created_at DESC
        """, (tmdb_id,))

    def get_user_movie_details(self, user_id: int, tmdb_id: int):
        """Pobiera ocenę i komentarz użytkownika dla konkretnego filmu."""
        return self.db.fetch_one("""
            SELECT 
                m.rating, 
                m.watched_at,
                c.content AS comment
            FROM movies m
            LEFT JOIN comments c ON m.user_id = c.user_id AND m.tmdb_id = c.tmdb_id
            WHERE m.user_id = ? AND m.tmdb_id = ?
        """, (user_id, tmdb_id))

    def get_user_movies(self, user_id: int, order="watched_at"):
        """Pobiera Historię Obejrzanych wraz z datą obejrzenia i oceną."""
        return self.db.fetch_all(f"""
            SELECT 
                m.tmdb_id, 
                m.rating, 
                m.watched_at, 
                mc.title, 
                mc.poster_path,
                -- Sprawdzamy czy film jest w historii (zawsze True tutaj, bo to historia)
                1 AS is_watched,
                -- Sprawdzamy czy film istnieje w tabeli watchlist dla tego użytkownika
                CASE WHEN w.tmdb_id IS NOT NULL THEN 1 ELSE 0 END AS is_on_watchlist
            FROM movies m
            JOIN movies_cache mc ON m.tmdb_id = mc.tmdb_id
            LEFT JOIN watchlist w ON m.tmdb_id = w.tmdb_id AND w.user_id = ?
            WHERE m.user_id = ?
            ORDER BY m.{order} DESC
        """, (user_id, user_id))

    def remove_from_watched(self, user_id: int, tmdb_id: int):
        """Usuwa obejrzany film oraz powiązane z nim dane."""
        self.db.execute("DELETE FROM movies WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))
        self.db.execute("DELETE FROM comments WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))

    def is_watched(self, user_id: int, tmdb_id: int) -> bool:
        """Zwraca True/False w zależności od tego czy użytkownik obejrzał dany film."""
        q = self.db.fetch_one("SELECT 1 FROM movies WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))
        return q is not None
