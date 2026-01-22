from models.movie import Movie
from typing import Any


class MovieUserData:
    def __init__(self, db) -> None:
        self.db = db

    def get_movie_from_cache(self, tmdb_id: int):
        """Zwraca dane z cache jeśli istnieją, w przeciwnym razie None."""
        return self.db.fetch_one(
            "SELECT title, poster_path FROM movies_cache WHERE tmdb_id = ?", 
            (tmdb_id,)
        )

    def _update_cache(self, tmdb_id: int, title: str, poster_path: str, genres: list[dict]):
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

        if genres:
            for genre in genres:
                g_id = genre['id']
                g_name = genre['name']
                
                self.db.execute(
                    "INSERT OR IGNORE INTO genres (id, name) VALUES (?, ?)", 
                    (g_id, g_name)
                )
                
                self.db.execute(
                    "INSERT OR IGNORE INTO movie_genres (tmdb_id, genre_id) VALUES (?, ?)",
                    (tmdb_id, g_id)
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

    def get_user_genres(self, user_id: int):
        """Pobiera listę unikalnych gatunków z filmów użytkownika."""
        return self.db.fetch_all("""
            SELECT DISTINCT g.name
            FROM genres g
            JOIN movie_genres mg ON g.id = mg.genre_id
            JOIN movies m ON mg.tmdb_id = m.tmdb_id
            WHERE m.user_id = ?
            ORDER BY g.name ASC
        """, (user_id,))

    def get_user_movies(self, user_id: int, genre_filter: str | None = None, sort_by: str ="newest"):
        """Pobiera Historię Obejrzanych wraz z datą obejrzenia i oceną."""

        sort_options = {
            "newest": "m.watched_at DESC",  # od najnowszych
            "oldest": "m.watched_at ASC",   # od najstarszych
            "rating_desc": "m.rating DESC", # najlepsze oceny
            "rating_asc": "m.rating ASC"    # najgorsze oceny
        }

        order = sort_options.get(sort_by, "m.watched_at DESC")

        sql = f"""
            SELECT 
                m.tmdb_id, 
                m.rating, 
                m.watched_at, 
                mc.title, 
                mc.poster_path,
                1 AS is_watched,
                CASE WHEN w.tmdb_id IS NOT NULL THEN 1 ELSE 0 END AS is_on_watchlist,
                GROUP_CONCAT(g.name, ',' ) as genres_str
            FROM movies m
            JOIN movies_cache mc ON m.tmdb_id = mc.tmdb_id
            LEFT JOIN watchlist w ON m.tmdb_id = w.tmdb_id AND w.user_id = ?
            LEFT JOIN movie_genres mg ON mg.tmdb_id = mc.tmdb_id
            LEFT JOIN genres g ON g.id = mg.genre_id
            WHERE m.user_id = ?
        """
        params: list[Any] = [user_id, user_id]

        if genre_filter and genre_filter != "all":
            sql += """
            AND EXISTS (
                SELECT 1 FROM movie_genres mg2 
                JOIN genres g2 ON mg2.genre_id = g2.id 
                WHERE mg2.tmdb_id = m.tmdb_id AND g2.name = ?
            )
            """
            params.append(genre_filter)

        sql += f" GROUP BY m.tmdb_id ORDER BY {order}"
        
        return self.db.fetch_all(sql, tuple(params))

    def remove_from_watched(self, user_id: int, tmdb_id: int):
        """Usuwa obejrzany film oraz powiązane z nim dane."""
        self.db.execute("DELETE FROM movies WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))
        self.db.execute("DELETE FROM comments WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))

    def is_watched(self, user_id: int, tmdb_id: int) -> bool:
        """Zwraca True/False w zależności od tego czy użytkownik obejrzał dany film."""
        q = self.db.fetch_one("SELECT 1 FROM movies WHERE user_id = ? AND tmdb_id = ?", (user_id, tmdb_id))
        return q is not None
