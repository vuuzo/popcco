from flask import Flask, flash, redirect, render_template, request, session, url_for, g
from db.database import Database
from db.repos.list_repo import ListRepo
from db.repos.movie_user_data import MovieUserData
from db.repos.user_repo import UserRepo
from db.repos.watchlist_repo import WatchlistRepo
from repos.movies_repo import MovieRepository
from services.security import SecurityMiddleware
from services.tmdb_adapter import TMDBAdapter
from services.tmdb_service import TMDBService
from services.cloudinary import CloudinaryService
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
FLASK_SECRET = os.getenv("FLASK_SECRET")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

_cloudinary_service = CloudinaryService(
    CLOUDINARY_CLOUD_NAME, 
    CLOUDINARY_API_KEY, 
    CLOUDINARY_API_SECRET
)

app = Flask(__name__)
app.secret_key = FLASK_SECRET

db = Database()

_movie_user_data = MovieUserData(db)
_watchlist_repo = WatchlistRepo(db)
_list_repo = ListRepo(db)
_tmdb_service = TMDBService(API_KEY)
_tmdb_adapter = TMDBAdapter(_tmdb_service)

# middleware
SecurityMiddleware(app)

# bezpośrednio do logowania/rejestracji
user_repo = UserRepo(db)


# GŁÓWNY SERWIS
watched = MovieRepository(_tmdb_adapter, _movie_user_data, _watchlist_repo, _list_repo)


@app.before_request
def load_user():
    """
    Pobiera użytkownika z bazy na podstawie sesji i zapisuje w g.user.
    Dzięki temu w każdym szablonie HTML mamy dostęp do {{ g.user }}.
    """
    user_id = session.get("user_id")
    
    if user_id:
        g.user = user_repo.get_by_id(user_id)
    else:
        g.user = None

@app.route("/")
def index():
    popular_movies = watched.get_popular_movies()
    return render_template("index.html", movies=popular_movies)


# =============
# AUTH
# =============

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Pola nie mogą być puste", "error")
            return redirect(url_for("login"))

        user = user_repo.get_by_username(username)

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("index"))
        else:
            flash("Hasło lub nazwa konta są błędne", "error")
        
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        re_password = request.form.get("repassword", "")
        
        if not username or not password or not re_password:
            flash("Pola nie mogą być puste", "error")
            return redirect(url_for("register"))

        if password != re_password:
            flash("Hasła nie są identyczne", "error")
            return redirect(url_for("register"))

        if user_repo.get_by_username(username):
            flash("Użytkownik o takiej nazwie już istnieje", "error")
            return redirect(url_for("register"))
            
        user_repo.create(username, password)
        return redirect(url_for("login"))
        
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# =============
# USER
# =============

@app.route("/profile/<username>")
def profile(username):
    profile_user = user_repo.get_by_username(username)
    
    if not profile_user:
        flash("Użytkownik nie istnieje", "error")
        return redirect(url_for('index'))

    viewer_id = session.get("user_id")
    is_owner = False

    stats = user_repo.get_all_user_stats(profile_user.id)
    
    if viewer_id:
        is_owner = (int(viewer_id) == profile_user.id)

    return render_template("profile.html", 
                           user=profile_user, 
                           is_owner=is_owner,
                           stats=stats)

@app.route("/profile/upload", methods=["POST"])
def upload_avatar():
    user_id = int(session["user_id"])
    username = session.get("username")

    if 'avatar' not in request.files:
        flash("Nie przesłano pliku", "error")
        return redirect(url_for('profile'))
    
    file = request.files['avatar']
    
    unique_filename = f"user_{user_id}"
    
    image_url = _cloudinary_service.upload(file, user_id=unique_filename)

    if image_url:
        user_repo.update_avatar(user_id, image_url)
        session["avatar"] = image_url 
        flash("Zdjęcie profilowe zaktualizowane!", "success")

    return redirect(url_for('profile', username=username))

# def upload_avatar():
#     user_id = int(session["user_id"])
#
#     if 'avatar' not in request.files:
#         flash("Nie przesłano pliku", "error")
#         return redirect(url_for('profile'))
#
#     file = request.files['avatar']
#
#     unique_filename = f"user_{user_id}"
#
#     image_url = _cloudinary_service.upload(file, user_id=unique_filename)
#
#     if image_url:
#         # WRÓĆ
#         # Ponieważ URL może być keszowany przez przeglądarkę, warto dodać
#         # na końcu losowy parametr (np. timestamp), żeby wymusić odświeżenie w HTML.
#         # Ale w bazie zapisujemy czysty URL.
#         user_repo.update_avatar(user_id, image_url)
#         flash("Zdjęcie profilowe zaktualizowane!", "success")
#     else:
#         flash("Wystąpił błąd podczas wysyłania zdjęcia.", "error")
#
#     return redirect(url_for('profile'))

# =============
# MOVIES
# =============

@app.route("/movies")
def movies():
    user_id = int(session["user_id"])

    user_movies = watched.get_user_movies(user_id)
    
    return render_template("movies.html", movies=user_movies)

@app.route("/movie/<int:id>")
def movie(id):
    user_id = session.get("user_id")

    movie = watched.get_movie_details(id, user_id)
    comments = watched.get_comments(id)
    user_lists = watched.get_user_lists(user_id) if user_id else []

    return render_template("movie.html", 
                           movie=movie, 
                           comments=comments, 
                           lists=user_lists)

@app.route("/movie/<int:movie_id>/add_comment", methods=["POST"])
def add_comment(movie_id):
    user_id = int(session["user_id"])

    content = request.form.get("content", "").strip()
    
    if not content:
        flash("Komentarz nie może być pusty", "error")
    else:
        watched.add_comment(user_id, movie_id, content)
        flash("Twój komentarz został zapisany", "success")

    return redirect(url_for('movie', id=movie_id))

@app.route("/movie/<int:movie_id>/remove_comment", methods=["POST"])
def remove_comment(movie_id):
    user_id = int(session["user_id"])

    watched.remove_comment(user_id, movie_id)
    flash("Komentarz został usunięty", "success")
    
    return redirect(url_for('movie', id=movie_id))


# =============
# SEARCH
# =============

@app.route("/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return redirect(url_for("index"))
    
    page = request.args.get("page", 1, type=int)
    search_data = watched.search(query, page)
    
    return render_template("search.html", search_data=search_data, query=query)


# =============
# WATCHLIST
# =============

@app.route("/watchlist")
def watchlist():
    user_id = int(session["user_id"])

    movies = watched.get_user_watchlist(user_id)

    for movie in movies:
        print(movie.is_watched)

    return render_template("watchlist.html", movies=movies)

@app.route("/add_to_watchlist/<int:movie_id>", methods=["POST"])
def add_to_watchlist(movie_id):
    user_id = int(session["user_id"])

    success = watched.add_to_watchlist(user_id, movie_id)
    
    if success:
        flash("Dodano do obejrzenia", "success")
    else:
        flash("Ten film już jest na liście", "error")

    return redirect(request.referrer)

@app.route("/remove_from_watchlist/<int:movie_id>", methods=["POST"])
def remove_from_watchlist(movie_id):
    user_id = int(session["user_id"])

    watched.remove_from_watchlist(user_id, movie_id)
    return redirect(request.referrer)


@app.route("/mark_watched/<int:movie_id>", methods=["POST"])
def mark_watched(movie_id):
    user_id = int(session["user_id"])

    rating = request.form.get('rating', type=int)
    is_update = watched.mark_as_watched(user_id, movie_id, rating)
    
    if is_update:
        flash("Ocena została zaktualizowana", "success")
    else:
        flash("Film dodany do obejrzanych", "success")

    return redirect(request.referrer)


@app.route("/remove_watched/<int:movie_id>", methods=["POST"])
def remove_watched(movie_id):
    user_id = int(session["user_id"])

    watched.remove_from_watched(user_id, movie_id)
    
    flash("Film został usunięty z obejrzanych", "success")
    return redirect(request.referrer or url_for('movies'))


# =============
# LISTS
# =============

@app.route("/lists", methods=["GET"])
def lists():
    user_id = session.get("user_id")

    lists = watched.get_all_lists()
    user_lists = watched.get_user_lists(user_id) if user_id else None

    return render_template("lists.html", lists=lists, user_lists=user_lists)

@app.route("/list/new", methods=["POST", "GET"])
def create_list():
    user_id = int(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if name:
            watched.create_list(user_id, name, description)
            flash(f"Lista '{name}' została utworzona", "success")
            return redirect(url_for('lists'))
        
        flash("Nazwa listy nie może być pusta", "error")
    
    return render_template("create_list.html")

@app.route("/add_to_list/<int:movie_id>", methods=["POST"])
def add_to_list(movie_id):
    user_id = int(session["user_id"])
    list_id = request.form.get("list_id")

    if list_id:
        watched.add_to_list(int(list_id), user_id, movie_id)
        flash("Dodano do listy", "success")

    return redirect(url_for('movie', id=movie_id))

@app.route("/list/<int:list_id>")
def list_details(list_id):
    user_id = session.get("user_id")

    custom_list = watched.get_list_details(list_id)
    if not custom_list:
        flash(f"Lista nie istnieje", "error")
        return redirect(url_for('lists'))

    movies = watched.get_list_movies(list_id)
    is_owner = user_id and custom_list["user_id"] == user_id

    return render_template("list_details.html", 
                           list=custom_list, 
                           movies=movies,
                           is_owner=is_owner)


@app.route("/list/<int:list_id>/remove", methods=["POST"])
def remove_list(list_id):
    user_id = int(session["user_id"])

    success = watched.delete_list(list_id, user_id)
    if success:
        flash("Lista została usunięta", "success")
        return redirect(url_for('lists'))

    flash("Błąd usuwania listy", "error")
    return redirect(url_for('index'))


@app.route("/list/<int:list_id>/remove/<int:movie_id>", methods=["POST"])
def remove_from_list(list_id, movie_id):
    user_id = int(session["user_id"])

    success = watched.remove_from_list(list_id, user_id, movie_id)
    if success:
        flash("Film usunięty z listy", "success")
    else:
        flash("Nie masz uprawnień", "error")
        
    return redirect(url_for('list_details', list_id=list_id))


if __name__ in "__main__":
    app.run(debug=True)

