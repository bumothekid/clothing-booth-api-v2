from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict

class OutfitTags(str, Enum):
    CASUAL = "Casual"
    FORMAL = "Formal"
    SPORTS = "Sports"
    VINTAGE = "Vintage"
    OUTDOOR = "Outdoor"
    PARTY = "Party"
    WORK = "Work"
    BEACH = "Beach"

class OutfitSeason(str, Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

@dataclass
class Outfit:
    outfit_id: str
    is_public: bool
    is_favorite: bool
    name: str
    created_at: datetime
    user_id: str
    clothing_ids: list[str]
    seasons: Optional[list[OutfitSeason]] = None
    tags: Optional[list[OutfitTags]] = None
    description: Optional[str] = None
        
    def to_dict(self) -> dict:
        data = asdict(self)
        
        if isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        return data
