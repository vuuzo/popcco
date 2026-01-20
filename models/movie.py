from datetime import datetime

class Movie:
    def __init__(self, tmdb_id: int):
        self.tmdb_id = tmdb_id

        # TMDB API
        self.title = None
        self.poster_path = None
        self.description = None
        self.director = None
        self.genres = []

        # SQLite
        self.watched_at: datetime | None = None

    def __str__(self):
        return f"[{self.tmdb_id}] {self.title}"

