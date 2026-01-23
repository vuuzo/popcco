from dataclasses import dataclass, field
from models.movie import Movie

@dataclass
class MovieSearchResult:
    page: int
    total_results: int
    total_pages: int
    results: list[Movie] = field(default_factory=list)
    params: dict = field(default_factory=dict)

    @classmethod
    def from_tmdb(cls, data: dict):
        movies = [Movie.from_tmdb(item) for item in data.get('results', [])]
        
        return cls(
            page=data.get('page', 1),
            total_results=data.get('total_results', 0),
            total_pages=data.get('total_pages', 1),
            results=movies
        )
