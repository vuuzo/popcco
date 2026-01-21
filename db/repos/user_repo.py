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

    # def login(self, username: str, password: str):
    #     row = self.db.fetch_one(
    #         "SELECT * FROM users WHERE username = ?",
    #         (username,)
    #     )
    #
    #     if row and check_password_hash(row["password"], password):
    #         return User(row["id"], row["username"])
    #     return None

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
