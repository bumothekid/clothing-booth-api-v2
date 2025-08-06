from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

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
    createdAt: datetime
    user_id: str
    image: str
    seasons: Optional[list[ClothingSeason]] = None
    tags: Optional[list[ClothingTags]] = None
    description: Optional[str] = None
        
    def to_dict(self) -> dict:
        return {
            "clothing_id": self.clothing_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "color": self.color,
            "seasons": [season.value for season in self.seasons],
            "tags": [tag.value for tag in self.tags],
            "created_at": self.createdAt.isoformat(),
            "image": self.image,
            "user_id": self.user_id
        }
