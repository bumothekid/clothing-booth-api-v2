from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict

class ClothingTags(str, Enum):
    CASUAL = "Casual"
    FORMAL = "Formal"
    SPORTS = "Sports"
    VINTAGE = "Vintage"
    OUTDOOR = "Outdoor"
    PARTY = "Party"
    WORK = "Work"
    BEACH = "Beach"
    
class ClothingSeason(str, Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"
    
class ClothingCategory(str, Enum):
    # Tops
    TSHIRT = "T-Shirt"
    SHIRT = "Shirt"
    POLO = "Polo"
    SWEATER = "Sweater"
    HOODIE = "Hoodie"
    JACKET = "Jacket"
    COAT = "Coat"
    # Bottoms
    JEANS = "Jeans"
    SHORTS = "Shorts"
    PANTS = "Pants"
    SKIRT = "Skirt"
    # Footwear
    SNEAKERS = "Sneakers"
    BOOTS = "Boots"
    SANDALS = "Sandals"
    HEELS = "Heels"
    LOAFERS = "Loafers"
    # Accessories
    HAT = "Hat"
    SCARF = "Scarf"
    GLOVES = "Gloves"
    BELT = "Belt"
    BAG = "Bag"
    WATCH = "Watch"
    ACCESSORY = "Accessory"

@dataclass
class Clothing:
    clothing_id: str
    is_public: bool
    name: str
    category: ClothingCategory
    color: str
    created_at: datetime
    user_id: str
    image_id: str
    seasons: Optional[list[ClothingSeason]] = None
    tags: Optional[list[ClothingTags]] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        
        if isinstance(data["created_at"], datetime):
            data["created_at"] = data["created_at"].replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        return data
    
    @classmethod
    def from_dict(self, core: dict, seasons: Optional[list[ClothingSeason]], tags: Optional[list[ClothingTags]]):
        return Clothing(
            clothing_id=core.get("clothing_id"),
            is_public=bool(core.get("is_public")),
            name=core.get("name"),
            color=core.get("color"),
            category=ClothingCategory[core.get("category")],
            created_at=core.get("created_at"),
            user_id=core.get("user_id"),
            image_id=core.get("image_id"),
            seasons=seasons,
            tags=tags,
            description=core.get("description")
            )
