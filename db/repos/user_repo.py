from models.user import User
from werkzeug.security import check_password_hash, generate_password_hash

class UserRepo:
    def __init__(self, db) -> None:
        self.db = db

    def create(self, username: str, password: str):
        password = generate_password_hash(password)
        self.db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
        )

    def get_by_username(self, username: str) -> User | None:
        """Pobiera użytkownika po nazwie."""
        row =  self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        if row:
            return User.from_db_row(row)
        return None


    def get_by_id(self, user_id: int) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        )
        if row:
            return User.from_db_row(row)
        return None

    def get_all_user_stats(self, user_id: int):
        sql = """
            SELECT 
                (SELECT COUNT(*) FROM lists WHERE user_id = ?) as lists_count,
                (SELECT COUNT(*) FROM movies WHERE user_id = ?) as watched_count,
                (SELECT COUNT(*) FROM watchlist WHERE user_id = ?) as watchlist_count,
                (SELECT COUNT(*) FROM comments WHERE user_id = ?) as comments_count
        """
        row = self.db.fetch_one(sql, (user_id, user_id, user_id, user_id))
        
        return dict(row) if row else {
            "lists_count": 0, "watched_count": 0, "watchlist_count": 0, "comments_count": 0
        }

    def update_avatar(self, user_id: int, avatar_url: str):
        self.db.execute(
            "UPDATE users SET avatar_url = ? WHERE id = ?",
            (avatar_url, user_id)
        )
