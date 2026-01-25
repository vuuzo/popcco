import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

    def __init__(self):
        api_key = os.getenv("TMDB_API_KEY")
        if not api_key:
            raise ValueError("Nie znaleziono zmiennej środowiskowej TMDB_API_KEY")

        self.session = requests.Session()
        
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }) 

    def _safe_get(self, url, params=None) -> dict:
        """Wspólna metoda do bezpiecznych zapytań"""
        try:
            res = self.session.get(url, params=params, timeout=5)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Błąd TMDB Service: {e}")
            return {}

    def search(self, query: str, page=1):
        return self._safe_get(f"{self.BASE_URL}/search/movie", {
            "query": query, 
            "page": page
        })

    def get_popular_movies(self):
        """Nowa metoda potrzebna dla widoku gościa"""
        return self._safe_get(f"{self.BASE_URL}/movie/popular")

    def get_movie(self, tmdb_id: int) -> dict:
        return self._safe_get(f"{self.BASE_URL}/movie/{tmdb_id}")

    def get_image_url(self, path: str | None, size="w342") -> str | None:
        if not path:
            return None
        if path.startswith("/static"):
            return path
        
        return f"https://image.tmdb.org/t/p/{size}{path}"
