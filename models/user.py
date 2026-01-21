# class User:
#     def __init__(self, id: int, username: str) -> None:
#         self.id = id
#         self.username = username

from dataclasses import dataclass
from werkzeug.security import check_password_hash

@dataclass
class User:
    id: int
    username: str
    password_hash: str

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
                password_hash=row_dict['password']
            )
        
        # Fallback: Jeśli row to zwykła krotka (tuple), używamy indeksów.
        # Zakładamy kolejność w bazie: id (0), username (1), password (2)
        else:
            return cls(
                id=row[0],
                username=row[1],
                password_hash=row[2]
            )

    def check_password(self, password: str) -> bool:
        """Sprawdza, czy podane hasło pasuje do hasha użytkownika"""
        # --- DEBUG START ---
        print(f"DEBUG LOGOWANIA:")
        print(f"Hasło w bazie (hash): {self.password_hash}")
        print(f"Hasło wpisane (text): {password}")
        result = check_password_hash(self.password_hash, password)
        print(f"Wynik sprawdzenia: {result}")
        # --- DEBUG END ---
        return result
        # return check_password_hash(self.password_hash, password)
