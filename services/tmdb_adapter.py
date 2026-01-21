from typing import Any
from services.tmdb_service import TMDBService

class TMDBAdapter:
    def __init__(self, tmdb_service: TMDBService):
        self.tmdb = tmdb_service

    def search_movies(self, query: str, page=1) -> dict[str, Any]:
        """Pobiera wyniki wyszukiwania"""
        return self.tmdb.search(query, page)
        # WRÓĆ
        # return [
        #     MovieSearchResult(
        #         tmdb_id=r["id"],
        #         title=r.get("title") or r.get("original_title") or "Nieznany tytuł",
        #         release_date =r.get("release_date") or None,
        #         poster_path=r.get("poster_path") if r.get("poster_path") else "/static/images/no_image.svg"
        #         # poster_path=r.get("poster_path") or None
        #     )
        #     for r in results
        # ]

    def get_popular(self) -> dict[str, Any]:
        """Pobiera popularne filmy"""
        return self.tmdb.get_popular_movies()

    def get_movie(self, tmdb_id: int) -> dict[str, Any]:
        """Pobiera szczegóły filmu"""
        return self.tmdb.get_movie(tmdb_id)

