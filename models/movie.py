from dataclasses import dataclass, field

@dataclass
class Movie:
    tmdb_id: int
    title: str | None = None
    poster_path: str = "/static/images/no_image.svg"
    description: str | None = None
    release_date: str | None = None
    rating: int | None = None
    watched_at: str | None = None
    is_on_watchlist: bool = False
    genres: list[str] = field(default_factory=list)


    @property
    def is_watched(self) -> bool:
        return self.watched_at is not None

    @classmethod
    def from_db_row(cls, row):
        """Tworzy obiekt na podstawie wiersza z bazy."""
        row_dict = dict(row) 

        genres_str = row_dict.get('genres_str')
        genres_list = genres_str.split(', ') if genres_str else []

        return cls(
            tmdb_id=row_dict['tmdb_id'],
            title=row_dict.get('title'),
            poster_path=row_dict.get('poster_path') or "/static/images/no_image.svg",
            rating=row_dict.get('rating'),
            watched_at=row_dict.get('watched_at'),
            is_on_watchlist=bool(row_dict.get('is_on_watchlist', 0)),
            genres=genres_list
        )

    @classmethod
    def from_tmdb(cls, data):
        """Tworzy obiekt na podstawie danych z API TMDB."""
        genres_data = data.get('genres', [])
        genres_names = [genre['name'] for genre in genres_data]

        return cls(
            tmdb_id=data.get('id'),
            title=data.get('title') or data.get('original_title') or "Nieznany tytuł",
            poster_path=data.get('poster_path') or "/static/images/no_image.svg",
            description=data.get('overview', ''),
            release_date=data.get('release_date'),
            genres=genres_names
        )

    def __str__(self):
        return f"[{self.tmdb_id}] {self.title}"
