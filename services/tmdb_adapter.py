from typing import Any
from services.tmdb_service import TMDBService

class TMDBAdapter:
    def __init__(self, tmdb_service: TMDBService):
        self.tmdb = tmdb_service

    def search_movies(self, query: str, page=1) -> dict[str, Any]:
        """Pobiera wyniki wyszukiwania"""
        return self.tmdb.search(query, page)

    def get_popular(self) -> dict[str, Any]:
        """Pobiera popularne filmy"""
        return self.tmdb.get_popular_movies()

    def get_movie(self, tmdb_id: int) -> dict[str, Any]:
        """Pobiera szczegóły filmu"""
        return self.tmdb.get_movie(tmdb_id)

