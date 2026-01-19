import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

    def __init__(self, api_key):
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
        """Wspólna metoda do bezpiecznych zapytań."""
        try:
            res = self.session.get(url, params=params, timeout=5)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"Błąd TMDB Service: {e}")
            return {}

    def search(self, query: str):
        data = self._safe_get(f"{self.BASE_URL}/search/movie", params={"query": query})
        return data.get("results", []) if data else []

    def get_movie(self, tmdb_id: int) -> dict:
        return self._safe_get(f"{self.BASE_URL}/movie/{tmdb_id}")

    # def __init__(self, api_key):
    #     self.session = requests.session()
    #     self.session.headers.update({
    #         "accept": "application/json",
    #         "Authorization": f"Bearer {api_key}"
    #     }) 
    #
    # def search(self, query: str):
    #     res = self.session.get(
    #             f"{self.BASE_URL}/search/movie",
    #             params={
    #                 "query": query,
    #                 "language": "en-US"
    #                 }
    #             )
    #     res.raise_for_status()
    #     return res.json().get("results", [])
    #
    # def get_movie(self, tmdb_id: int) -> dict:
    #     res = self.session.get(
    #         f"{self.BASE_URL}/movie/{tmdb_id}",
    #         params={
    #             "language": "en-US"
    #         }
    #     )
    #     res.raise_for_status()
    #     return res.json()

    def get_poster_url(self, poster_path: str | None) -> str | None:
        if not poster_path:
            return None
        if poster_path.startswith("/static"):
            return poster_path

        return f"{self.IMAGE_BASE_URL}{poster_path}"
