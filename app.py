from flask import Flask, flash, redirect, render_template, request, session, url_for
from db.database import Database
from db.repos.list_repo import ListRepo
from db.repos.movie_user_data import MovieUserData
from db.repos.user_repo import UserRepo
from db.repos.watchlist_repo import WatchlistRepo
from repos.movies_repo import MovieRepository
from services.tmdb_adapter import TMDBAdapter
from services.tmdb_service import TMDBService
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
FLASK_SECRET = os.getenv("FLASK_SECRET")


app = Flask(__name__)
app.secret_key = FLASK_SECRET

db = Database()
movie_user_data = MovieUserData(db)
user_repo = UserRepo(db)
tmdb_service = TMDBService(API_KEY)
tmdb = TMDBAdapter(tmdb_service)
watchlist_repo = WatchlistRepo(db)
list_repo = ListRepo(db)
watched = MovieRepository(tmdb, movie_user_data, watchlist_repo, list_repo)

# middleware
@app.before_request
def security_layer():
    auth_routes = ['login', 'register']
    public_routes = ['index', 'static', 'logout', 'movie', 'search', 'lists', 'list_details']
    
    endpoint = request.endpoint
    
    if not endpoint:
        return

    is_logged_in = 'user_id' in session

    # Blokada dla zalogowanych
    if is_logged_in and endpoint in auth_routes:
        return redirect(url_for('index'))

    # Blokada dla niezalogowanych
    if not is_logged_in and endpoint not in (public_routes + auth_routes):
        return redirect(url_for('login'))


@app.route("/")
def index():
    return render_template("index.html")



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

        user = user_repo.login(username, password)

        if user:
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
# MOVIES
# =============

@app.route("/movies")
def movies():
    user_id = session.get("user_id")
    if not user_id:
        flash("Musisz się zalogować.")
        return redirect(url_for('login'))

    user_movies = movie_user_data.get_user_movies(user_id)
    
    return render_template("movies.html", movies=user_movies)

@app.route("/movie/<int:id>")
def movie(id):
    result = tmdb.get_movie(id)
    comments = movie_user_data.get_all_comments(id)
    
    user_data = None
    on_watchlist = False
    user_lists = None

    user_id = session.get("user_id")
    if user_id:
        user_data = movie_user_data.get_user_movie_details(user_id, id)
        user_lists = list_repo.get_user_lists(user_id)
        on_watchlist = watchlist_repo.is_on_watchlist(user_id, id)

    return render_template("movie.html", 
                           movie=result, 
                           comments=comments,
                           user_data=user_data, 
                           lists=user_lists,
                           on_watchlist=on_watchlist)

@app.route("/movie/<int:movie_id>/add_comment", methods=["POST"])
def add_comment(movie_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Musisz się zalogować, aby dodać komentarz", "error")
        return redirect(url_for('login'))

    content = request.form.get("content", "").strip()
    
    if not content:
        flash("Komentarz nie może być pusty", "error")
    else:
        movie_user_data.add_comment(user_id, movie_id, content)
        flash("Twój komentarz został zapisany", "success")

    return redirect(url_for('movie', id=movie_id))

@app.route("/movie/<int:movie_id>/remove_comment", methods=["POST"])
def remove_comment(movie_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('login'))

    movie_user_data.remove_comment(user_id, movie_id)
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
    
    results = tmdb.search_movies(query)
    
    return render_template("search.html", results=results, query=query)


# =============
# WATCHLIST
# =============

@app.route("/watchlist")
def watchlist():
    user_id = session.get('user_id')
    if not user_id:
        flash("Musisz się zalogować", "error")
        return redirect(url_for('login'))

    movies = watchlist_repo.get(user_id)
    return render_template("watchlist.html", movies=movies)

@app.route("/add_to_watchlist/<int:movie_id>", methods=["POST"])
def add_to_watchlist(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Musisz się zalogować", "error")
        return redirect(url_for('login'))

    if watchlist_repo.is_on_watchlist(user_id, movie_id):
        flash("Ten film jest już na Twojej liście do obejrzenia", "error")
    else:
        watched.add_to_watchlist(user_id, movie_id)
        flash("Dodano do obejrzenia", "success")

    return redirect(request.referrer)

@app.route("/remove_from_watchlist/<int:movie_id>", methods=["POST"])
def remove_from_watchlist(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Musisz się zalogować", "error")
        return redirect(url_for('login'))

    watchlist_repo.remove(user_id, movie_id)
    return redirect(request.referrer)


@app.route("/mark_watched/<int:movie_id>", methods=["POST"])
def mark_watched(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    rating = request.form.get('rating', type=int)

    already_watched = movie_user_data.is_watched(user_id, movie_id)    
    watched.mark_as_watched(user_id, movie_id, rating)
    
    if already_watched:
        flash("Ocena została zaktualizowana", "success")
    else:
        watchlist_repo.remove(user_id, movie_id)
        flash("Film dodany do obejrzanych", "success")

    return redirect(request.referrer)


@app.route("/remove_watched/<int:movie_id>", methods=["POST"])
def remove_watched(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    movie_user_data.remove_from_watched(user_id, movie_id)
    
    flash("Film został usunięty z obejrzanych", "success")
    return redirect(request.referrer or url_for('movies'))


# =============
# LISTS
# =============

@app.route("/lists", methods=["GET"])
def lists():
    user_id = session.get("user_id")
    user_lists = None

    if user_id:
        user_lists = list_repo.get_user_lists(user_id)

    lists = list_repo.get_all_lists() 
    
    return render_template("lists.html", lists=lists, user_lists=user_lists)

@app.route("/list/new", methods=["POST", "GET"])
def create_list():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('login'))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        
        if name:
            list_repo.create_list(user_id, name, description)
            flash(f"Lista '{name}' została utworzona", "success")
            return redirect(url_for('lists'))
        
        flash("Nazwa listy nie może być pusta", "error")
    
    return render_template("create_list.html")

@app.route("/add_to_list/<int:movie_id>", methods=["POST"])
def add_to_list(movie_id):
    user_id = session.get("user_id")
    list_id = request.form.get("list_id")

    if user_id and list_id:
        watched.add_to_custom_list(int(list_id), user_id, movie_id)
        flash("Dodano do listy", "success")

    return redirect(url_for('movie', id=movie_id))

@app.route("/list/<int:list_id>")
def list_details(list_id):
    list = list_repo.get_list(list_id)
    is_owner = False
    
    if not list:
        flash(f"Lista nie istnieje", "error")
        return redirect(url_for('lists'))

    movies = list_repo.get_list_movies(list_id)

    user_id = session.get("user_id")
    if user_id and list and user_id == list['user_id']:
        is_owner = True

    return render_template("list_details.html", 
                           list=list, 
                           movies=movies,
                           is_owner=is_owner)


@app.route("/list/<int:list_id>/remove", methods=["POST"])
def remove_list(list_id):
    user_id = session.get("user_id")
    movie_list = list_repo.get_list(list_id)

    if user_id and movie_list and movie_list['user_id'] == user_id:
        list_repo.delete_list(list_id, user_id)
        flash("Lista została usunięta", "success")
        return redirect(url_for('lists'))
    
    return redirect(url_for('index'))

@app.route("/list/<int:list_id>/remove/<int:movie_id>", methods=["POST"])
def remove_from_list(list_id, movie_id):
    user_id = session.get("user_id")
    movie_list = list_repo.get_list(list_id) 
    
    if not user_id or not movie_list or movie_list['user_id'] != user_id:
        flash("Nie masz uprawnień", "error")
        return redirect(url_for('lists'))

    list_repo.remove_movie(list_id, movie_id)
    flash("Film usunięty z listy", "success")
    return redirect(url_for('list_details', list_id=list_id))

if __name__ in "__main__":
    app.run(debug=True)

