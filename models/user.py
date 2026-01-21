from dataclasses import dataclass
from werkzeug.security import check_password_hash

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    created_at: str
    bio: str | None = None
    avatar_url: str | None = None


    @property
    def display_avatar(self):
        """Zwraca avatar użytkownika lub domyślny obrazek"""
        return self.avatar_url or "/static/images/no_avatar.svg"

    @classmethod
    def from_db_row(cls, row):
        """Tworzy obiekt User z wiersza bazy danych"""
        # WRÓĆ
        # row_dict = dict(row)
        # return cls(
        #     id=row_dict['id'],
        #     username=row_dict['username'],
        #     password_hash=row_dict['password']
        # )
        # Sprawdzamy, czy row zachowuje się jak słownik (ma klucze)
        if hasattr(row, 'keys'):
            row_dict = dict(row)
            return cls(
                    id=row_dict['id'],
                    username=row_dict['username'],
                    created_at=row_dict['created_at'],
                    password_hash=row_dict['password'],
                    bio=row_dict['bio'],
                    avatar_url=row_dict.get('avatar_url')
                )
        
        # WRÓĆ
        # Fallback: Jeśli row to zwykła krotka (tuple), używamy indeksów.
        # Zakładamy kolejność w bazie: id (0), username (1), password (2)
        else:
            return cls(
                id=row[0],
                username=row[1],
                password_hash=row[2],
                bio=row[3],
                avatar_url=row[4] if len(row) > 4 else None,
                created_at=row[5]
            )

    def check_password(self, password: str) -> bool:
        """Sprawdza, czy podane hasło pasuje do hasha użytkownika"""
        return check_password_hash(self.password_hash, password)
