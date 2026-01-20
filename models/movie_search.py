class MovieSearchResult:
    def __init__(self, tmdb_id: int, title: str, release_date: str | None, poster_path: str | None):
        self.tmdb_id = tmdb_id
        self.title = title
        self.release_date = release_date
        self.poster_path = poster_path

    def __str__(self) -> str:
        return f"{self.tmdb_id:<10} ({self.release_date or "Brak":<10}) {self.title} [{self.poster_path}]"

