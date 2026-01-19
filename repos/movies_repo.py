from db.repos.list_repo import ListRepo
from db.repos.movie_user_data import MovieUserData
from db.repos.watchlist_repo import WatchlistRepo
from services.tmdb_adapter import TMDBAdapter

class MovieRepository:
    def __init__(self, tmdb: TMDBAdapter, user_data: MovieUserData, watchlist_repo: WatchlistRepo, list_repo: ListRepo):
        self.tmdb = tmdb
        self.user_data = user_data
        self.watchlist_repo = watchlist_repo
        self.list_repo = list_repo

    def _ensure_movie_info(self, tmdb_id: int):
        """
        Zapewnia, że dane o filmie są w cache.
        Jeśli ich nie ma - pobiera z API i zapisuje.
        """
        cached = self.user_data.get_movie_from_cache(tmdb_id)
        if cached:
            return

        api_data = self.tmdb.get_movie(tmdb_id)
        title = api_data.get('title') or "Nieznany Tytuł"
        poster = api_data.get('poster_path') or "/static/images/no_image.svg" 

        self.user_data._update_cache(tmdb_id, title, poster)

    def add_to_watchlist(self, user_id: int, tmdb_id: int):
        self._ensure_movie_info(tmdb_id)
        self.watchlist_repo.add(user_id, tmdb_id)

    def mark_as_watched(self, user_id: int, tmdb_id: int, rating: int | None = None):
        self._ensure_movie_info(tmdb_id)
        self.user_data.add_to_watched(user_id, tmdb_id, rating)

    def remove_from_watched(self, user_id: int, tmdb_id: int):
        """Usuwa film oraz powiązany z nim komentarz z danych użytkownika."""
        self.user_data.remove_from_watched(user_id, tmdb_id)

    def add_to_custom_list(self, list_id: int, user_id: int, tmdb_id: int):
        self._ensure_movie_info(tmdb_id)
        self.list_repo.add_movie_to_list(list_id, user_id, tmdb_id)
