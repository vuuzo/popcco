from dataclasses import dataclass
from typing import Optional

@dataclass
class Comment:
    content: str
    created_at: str
    updated_at: str
    username: str
    avatar_url: str = "/static/images/no_avatar.svg"
    rating: Optional[int] = None
    
    @property
    def display_avatar(self) -> str:
        """Zwraca avatar usera lub domyślny obrazek"""
        return self.avatar_url or "/static/images/no_avatar.svg"

    @classmethod
    def from_db_row(cls, row):
        """Tworzy obiekt Comment na podstawie wiersza z bazy"""
        row_dict = dict(row)
        
        return cls(
            content=row_dict['content'],
            created_at=row_dict['created_at'],
            updated_at=row_dict['updated_at'],
            username=row_dict['username'],
            avatar_url=row_dict.get('avatar_url') or "/static/images/no_avatar.svg",
            rating=row_dict.get('rating')
        )
