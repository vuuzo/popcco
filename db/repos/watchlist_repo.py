class WatchlistRepo:
    def __init__(self, db) -> None:
        self.db = db

    def add(self, user_id: int, tmdb_id: int):
        self.db.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, tmdb_id) VALUES (?, ?)",
            (user_id, tmdb_id)
        )

    def get(self, user_id: int):
        """Pobiera filmy z listy DO OBEJRZENIA."""
        return self.db.fetch_all("""
            SELECT 
                w.tmdb_id, 
                mc.title, 
                mc.poster_path,
                CASE WHEN m.id IS NOT NULL THEN 1 ELSE 0 END AS is_watched,
                1 AS is_on_watchlist
            FROM watchlist w
            JOIN movies_cache mc ON w.tmdb_id = mc.tmdb_id
            LEFT JOIN movies m ON w.user_id = m.user_id AND w.tmdb_id = m.tmdb_id
            WHERE w.user_id = ?
            ORDER BY w.id DESC
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
