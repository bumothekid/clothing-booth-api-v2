from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

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
        return {
            "outfit_id": self.outfit_id,
            "name": self.name,
            "description": self.description,
            "seasons": [season.value for season in self.seasons] if self.seasons is not None else None,
            "tags": [tag.value for tag in self.tags] if self.tags is not None else None,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "clothing_ids": self.clothing_ids
        }
