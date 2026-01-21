from flask import request, session, redirect, url_for

class SecurityMiddleware:
    """
    Klasa odpowiedzialna za kontrolę dostępu do stron.
    """
    def __init__(self, app):
        self.app = app
        
        self.auth_routes = {'login', 'register'}
        self.public_routes = {
            'index', 'static', 'logout', 'movie', 'search', 
            'lists', 'list_details', 'search', 'profile'
        }
        
        # Rejestrujemy hook w aplikacji
        self.app.before_request(self.check_access)

    def check_access(self):
        # WRÓĆ
        # endpoint = request.endpoint
        #
        # # Ignorujemy żądania bez endpointu
        # if not endpoint or endpoint == 'static':
        #     return

        if request.path.startswith('/static'):
            return

        endpoint = request.endpoint
        
        # Jeśli endpoint nie istnieje (np. 404), niech Flask się tym zajmie standardowo
        if not endpoint:
            return

        is_logged_in = 'user_id' in session

        # Zalogowany użytkownik nie powinien widzieć logowania/rejestracji
        if is_logged_in and endpoint in self.auth_routes:
            return redirect(url_for('index'))

        # Niezalogowany użytkownik nie wejdzie na strony, które
        # wymagają bycia zalogowanym
        is_public = endpoint in self.public_routes or endpoint in self.auth_routes
        
        if not is_logged_in and not is_public:
            return redirect(url_for('login'))
