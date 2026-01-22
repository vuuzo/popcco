from typing import Any

class WatchlistRepo:
    def __init__(self, db) -> None:
        self.db = db

    def add(self, user_id: int, tmdb_id: int):
        self.db.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, tmdb_id) VALUES (?, ?)",
            (user_id, tmdb_id)
        )

    def get(self, user_id: int, genre_filter: str | None = None, sort_by: str = "newest"):
        """Pobiera filmy z listy DO OBEJRZENIA."""

        sort_options = {
            "newest": "w.id DESC",
            "oldest": "w.id ASC",
            "a_z": "mc.title ASC",    # alfabetycznie
            "z_a": "mc.title DESC"
        }

        order = sort_options.get(sort_by, "w.id DESC")

        sql = """
            SELECT 
                w.tmdb_id, 
                mc.title, 
                mc.poster_path,
                m.watched_at,
                1 AS is_on_watchlist,
                GROUP_CONCAT(g.name, ', ') as genres_str
            FROM watchlist w
            JOIN movies_cache mc ON w.tmdb_id = mc.tmdb_id
            LEFT JOIN movies m ON w.user_id = m.user_id AND w.tmdb_id = m.tmdb_id
            LEFT JOIN movie_genres mg ON mc.tmdb_id = mg.tmdb_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE w.user_id = ?
        """
        
        params: list[Any] = [user_id]

        if genre_filter and genre_filter != 'all':
            sql += """
                AND EXISTS (
                    SELECT 1 FROM movie_genres mg2 
                    JOIN genres g2 ON mg2.genre_id = g2.id 
                    WHERE mg2.tmdb_id = w.tmdb_id AND g2.name = ?
                )
            """
            params.append(genre_filter)

        sql += f" GROUP BY w.tmdb_id ORDER BY {order}"
        
        return self.db.fetch_all(sql, tuple(params))

        # return self.db.fetch_all("""
        #     SELECT 
        #         w.tmdb_id, 
        #         mc.title, 
        #         mc.poster_path,
        #         m.watched_at,
        #         1 AS is_on_watchlist,
        #         GROUP_CONCAT(g.name, ', ') as genres_str
        #     FROM watchlist w
        #     JOIN movies_cache mc ON w.tmdb_id = mc.tmdb_id
        #     LEFT JOIN movies m ON w.user_id = m.user_id AND w.tmdb_id = m.tmdb_id
        #     LEFT JOIN movie_genres mg ON mg.tmdb_id = mc.tmdb_id
        #     LEFT JOIN genres g ON g.id = mg.genre_id
        #     WHERE w.user_id = ?
        #     GROUP BY w.tmdb_id
        #     ORDER BY w.id DESC
        # """, (user_id,))

    def get_watchlist_genres(self, user_id: int):
        return self.db.fetch_all("""
            SELECT DISTINCT g.name
            FROM genres g
            JOIN movie_genres mg ON g.id = mg.genre_id
            JOIN watchlist w ON mg.tmdb_id = w.tmdb_id
            WHERE w.user_id = ?
            ORDER BY g.name ASC
        """, (user_id,))

    def remove(self, user_id: int, tmdb_id: int):
        """Usuwa film z watchlisty (po obejrzeniu)."""
        self.db.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND tmdb_id = ?",
            (user_id, tmdb_id)
        )

    def is_on_watchlist(self, user_id: int, tmdb_id: int) -> bool:
        """Sprawdza czy dany film znajduje się na liście filmów do obejrzenia."""
        row = self.db.fetch_one(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND tmdb_id = ?",
            (user_id, tmdb_id)
        )
        return row is not None
