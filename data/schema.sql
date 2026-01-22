CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        bio TEXT,
        avatar_url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS movies_cache (
    tmdb_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    poster_path TEXT NOT NULL,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movie_genres (
    tmdb_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    FOREIGN KEY (tmdb_id) REFERENCES movies_cache(tmdb_id),
    FOREIGN KEY (genre_id) REFERENCES genres(id),
    PRIMARY KEY (tmdb_id, genre_id)
);

CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tmdb_id INTEGER NOT NULL,
        rating INTEGER,
        watched_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (tmdb_id) REFERENCES movies_cache(tmdb_id),
        UNIQUE (user_id, tmdb_id)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tmdb_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (tmdb_id) REFERENCES movies_cache(tmdb_id),
    UNIQUE (user_id, tmdb_id)
);

CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tmdb_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (tmdb_id) REFERENCES movies_cache(tmdb_id),
        UNIQUE (user_id, tmdb_id)
);

CREATE TABLE IF NOT EXISTS lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS list_movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        tmdb_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (list_id) REFERENCES lists(id),
        FOREIGN KEY (tmdb_id) REFERENCES movies_cache(tmdb_id),
        UNIQUE (list_id, tmdb_id)
);

CREATE TABLE IF NOT EXISTS list_followers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (list_id) REFERENCES lists(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
);

