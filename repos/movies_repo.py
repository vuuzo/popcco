from math import ceil
from db.repos.list_repo import ListRepo
from db.repos.movie_user_data import MovieUserData
from db.repos.watchlist_repo import WatchlistRepo
from models.movie_search import MovieSearchResult
from services.tmdb_adapter import TMDBAdapter
from models.movie import Movie

class MovieRepository:
    def __init__(self, 
                 tmdb_adapter: TMDBAdapter, 
                 movie_user_dao: MovieUserData, 
                 watchlist_dao: WatchlistRepo, 
                 list_dao: ListRepo):
        self.tmdb = tmdb_adapter
        self.user_dao = movie_user_dao
        self.watchlist_dao = watchlist_dao
        self.list_dao = list_dao

    def search(self, query: str, page=1) -> MovieSearchResult:
        raw_data = self.tmdb.search_movies(query, page)
        res = MovieSearchResult.from_tmdb(raw_data)
        res.params = {"q": query}

        return res
        # return MovieSearchResult.from_tmdb(raw_data)

    def _ensure_movie_info(self, tmdb_id: int):
        """
        Zapewnia, że dane o filmie są w cache.
        Jeśli ich nie ma - pobiera z API i zapisuje.
        """
        cached = self.user_dao.get_movie_from_cache(tmdb_id)
        if cached:
            return

        api_data = self.tmdb.get_movie(tmdb_id)
        title = api_data.get('title') or api_data.get('original_title') or "Nieznany Tytuł"
        poster = api_data.get('poster_path') or "/static/images/no_image.svg" 
        genres = api_data.get('genres', [])

        self.user_dao._update_cache(tmdb_id, title, poster, genres)

    # FILMY
    def get_movies_popular_db(self, limit: int = 3):
        """Zwraca N najpopularniejsze filmy z Popcco"""
        rows = self.user_dao.get_most_popular_movies(limit)
        return [Movie.from_db_row(row) for row in rows]

    def get_movies_popular_tmdb(self) -> list[Movie]:
        """Zwraca najpopularniejsze filmy z serwisu TMDB"""
        raw_data = self.tmdb.get_popular()
        return [Movie.from_tmdb(item) for item in raw_data.get('results', [])]

    def get_movie_details(self, tmdb_id: int, user_id: int | None = None) -> Movie:
        """Zwraca dane o filmie, jeśli user_id jest podane, uzupełnia o dane użytkownika"""

        tmdb_data = self.tmdb.get_movie(tmdb_id)
        movie = Movie.from_tmdb(tmdb_data)

        if user_id:
            user_details = self.user_dao.get_user_movie_details(user_id, tmdb_id)
            is_on_watchlist = self.watchlist_dao.is_on_watchlist(user_id, tmdb_id)
            
            movie.is_on_watchlist = is_on_watchlist
            if user_details:
                movie.rating = user_details['rating']
                movie.watched_at = user_details['watched_at']

        return movie

    def get_movie_stats(self, tmdb_id: int):
        """
        Zwraca statystyki filmu:
            avg_rating     -   ogólna ocena filmu
            rating_count   -   ilość ocen
            
        """
        return self.user_dao.get_movie_stats(tmdb_id)

    # KOMENTARZE
    def get_comments(self, tmdb_id: int):
        """Pobiera wszystkie komentarze pod filmem"""
        return self.user_dao.get_all_comments(tmdb_id)
        
    def add_comment(self, user_id: int, tmdb_id: int, content: str):
        """Dodaje komentarz"""
        self._ensure_movie_info(tmdb_id)
        self.user_dao.add_comment(user_id, tmdb_id, content)

    def remove_comment(self, user_id: int, tmdb_id: int):
        """Usuwa komentarz"""
        self.user_dao.remove_comment(user_id, tmdb_id)

    # LISTY
    def get_user_lists(self, user_id: int):
        """Zwraca listy stworzone przez usera"""
        return self.list_dao.get_user_lists(user_id)

    def get_lists(self, page = 1):
        """Zwraca wszystkie listy z bazy"""
        limit = 10
        rows = self.list_dao.get_all_lists(page=page, limit=limit)
        total_count = self.list_dao.count_all_lists()
        
        total_pages = ceil(total_count / limit)
        
        return {
            "items": rows,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "params": {} # listy nie mają filtrów, więc pusty słownik
        }

    def create_list(self, user_id: int, name: str, description: str):
        """Tworzy nową listę"""
        self.list_dao.create_list(user_id, name, description)

    def get_list_details(self, list_id: int):
        """Zwraca nazwę, opis oraz właściciela listy"""
        return self.list_dao.get_list(list_id)

    def get_list_movies(self, list_id: int) -> list[Movie]:
        """Pobiera filmy znajdujące się na danej liście"""
        # WRÓĆ
        # Tu też można by zmapować na obiekty Movie, na razie zwracamy surowe dane z repo
        return self.list_dao.get_list_movies(list_id)

    def add_to_list(self, list_id: int, user_id: int, tmdb_id: int):
        """Dodaje film do listy"""
        self._ensure_movie_info(tmdb_id)
        self.list_dao.add_movie_to_list(list_id, user_id, tmdb_id)

    def remove_from_list(self, list_id: int, user_id: int, tmdb_id: int):
        """Usuwa film z listy, sprawdza czy lista należy do użytkownika"""
        movie_list = self.list_dao.get_list(list_id)
        if not movie_list or movie_list['user_id'] != user_id:
            return False
            
        self.list_dao.remove_movie(list_id, tmdb_id)
        return True

    def delete_list(self, list_id: int, user_id: int) -> bool:
        """Usuwa listę"""
        movie_list = self.list_dao.get_list(list_id)
        if movie_list and movie_list['user_id'] == user_id:
            self.list_dao.delete_list(list_id, user_id)
            return True
        return False

    # DO OBEJRZENIA (WATCHLIST)
    def get_watchlist(self, user_id: int, genre: str | None = None, sort: str = "newest", page: int = 1):
        """Zwraca wszystkie filmy na 'Do Obejrzenia' usera"""
        limit = 20
        
        rows = self.watchlist_dao.get(user_id, genre_filter=genre, sort_by=sort, page=page, limit=limit)

        items = [Movie.from_db_row(row) for row in rows]

        total_count = self.watchlist_dao.count(user_id, genre_filter=genre)
        total_pages = ceil(total_count / limit)
        
        return {
            "items": items,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "params": {"genre": genre, "sort": sort} # zachowanie filtrów w url
        }

    def get_watchlist_genres(self, user_id: int):
        """Pobiera dostępne gatunki z watchlisty"""
        return self.watchlist_dao.get_watchlist_genres(user_id)

    def add_to_watchlist(self, user_id: int, tmdb_id: int) -> bool:
        """Dodaje do watchlisty"""
        if self.watchlist_dao.is_on_watchlist(user_id, tmdb_id):
            return False
        
        self._ensure_movie_info(tmdb_id)
        self.watchlist_dao.add(user_id, tmdb_id)
        return True

    def remove_from_watchlist(self, user_id: int, tmdb_id: int):
        """Usuwa film z watchlisty"""
        self.watchlist_dao.remove(user_id, tmdb_id)

    # OBEJRZANE
    def remove_from_watched(self, user_id: int, tmdb_id: int):
        """Usuwa film oraz powiązany z nim komentarz z danych usera"""
        self.user_dao.remove_from_watched(user_id, tmdb_id)

    def get_user_genres(self, user_id: int):
        """Zwraca listę wszystkich gatunków, jakie posiada user w swojej bibliotece"""
        return self.user_dao.get_user_genres(user_id)

    def get_user_movies(self, user_id: int, genre: str | None = None, sort: str = "newest", page: int = 1):
        """Zwraca filmy obejrzane przez usera"""
        limit = 18
        
        rows = self.user_dao.get_user_movies(user_id, genre_filter=genre, sort_by=sort, page=page, limit=limit)
        total_count = self.user_dao.count_user_movies(user_id, genre_filter=genre)
        
        total_pages = ceil(total_count / limit)

        return {
            "items": rows,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "params": {"genre": genre, "sort": sort}
        }

    def mark_as_watched(self, user_id: int, tmdb_id: int, rating: int | None = None) -> bool:
        """
        Zapisuje film jako obejrzany.
        Zwraca: True    jeśli to była aktualizacja (film już był obejrzany),
                False   jeśli to nowe obejrzenie (wtedy usuwa też z watchlisty).
        """
        already_watched = self.user_dao.is_watched(user_id, tmdb_id)
        
        self._ensure_movie_info(tmdb_id)
        self.user_dao.add_to_watched(user_id, tmdb_id, rating)
        
        self.watchlist_dao.remove(user_id, tmdb_id)

        if not already_watched:
            return False
        
        return True

    def follow_list(self, user_id: int, list_id: int):
        self.list_dao.follow_list(user_id, list_id)

    def unfollow_list(self, user_id: int, list_id: int):
        self.list_dao.unfollow_list(user_id, list_id)

    def get_user_followed_lists(self, user_id: int):
        """Zwraca listy obserwowane przez usera."""
        return self.list_dao.get_followed_lists(user_id)

    def get_list_stats(self, list_id: int, user_id: int | None):
        """Zwraca liczbę obserwujących oraz czy dany user obserwuje listę."""
        count = self.list_dao.get_followers_count(list_id)
        is_following = False
        if user_id:
            is_following = self.list_dao.is_following(user_id, list_id)
        
        return {
            "followers_count": count,
            "is_following": is_following
        }
