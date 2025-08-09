from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

@dataclass
class User:
    user_id: str
    is_guest: bool
    created_at: datetime
    updated_at: datetime
    username: Optional[str] = None
    email: Optional[str] = None
    profile_picture: Optional[str] = None
    
    def to_dict(self, exclude_none=True):
        d = asdict(self)
        if exclude_none:
            d = {k: v for k, v in d.items() if v is not None}
        return d
    
    @classmethod
    def from_dict(self, data: dict):
        return User(
            user_id=data.get("user_id"),
            is_guest=data.get("is_guest"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            username=data.get("username"),
            email=data.get("email"),
            profile_picture=data.get("profile_picture")
            )
