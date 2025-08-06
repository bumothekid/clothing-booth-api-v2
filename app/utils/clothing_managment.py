__all__ = ["clothing_manager"]

import traceback
import uuid
from re import match as re_match
from datetime import datetime
from app.utils.database import Database
from app.utils.exceptions import ClothingNotFoundError, ClothingImageInvalidError, ClothingNameMissingError, ClothingCategoryMissingError, ClothingColorMissingError, ClothingImageMissingError, ClothingNameTooShortError, ClothingNameTooLongError, ClothingDescriptionTooLongError, ClothingIDMissingError
from typing import Optional
from mysql.connector.errors import IntegrityError
from app.models.clothing import Clothing, ClothingCategory, ClothingSeason, ClothingTags
from app.utils.authentication_managment import authentication_manager
from app.utils.logging import get_logger
from app.utils.image_managment import image_manager
import os

logger = get_logger()

class ClothingManager:

    def ensure_table_exists(self) -> None:
        with Database.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS clothing(
                            clothing_id VARCHAR(36) PRIMARY KEY,
                            is_public BOOLEAN DEFAULT TRUE,
                            name VARCHAR(50) NOT NULL,
                            category VARCHAR(50) NOT NULL,
                            image VARCHAR(255) UNIQUE NOT NULL,
                            user_id VARCHAR(36) NOT NULL,
                            color CHAR(7) NOT NULL,
                            description VARCHAR(255) DEFAULT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                            );
                            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS clothing_seasons(
                            clothing_id VARCHAR(36) NOT NULL,
                            season ENUM('SPRING', 'SUMMER', 'AUTUMN', 'WINTER') NOT NULL,
                            FOREIGN KEY (clothing_id) REFERENCES clothing(clothing_id) ON DELETE CASCADE
                            );
                            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS clothing_tags(
                            clothing_id VARCHAR(36) NOT NULL,
                            tag VARCHAR(50) NOT NULL,
                            FOREIGN KEY (clothing_id) REFERENCES clothing(clothing_id) ON DELETE CASCADE
                            );
                            """)
            conn.commit()

    def _delete_unused_image(self, filename: str) -> None:
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM clothing WHERE image = %s;", (filename,))
                if cursor.fetchone() is not None:
                    return
            
            os.remove(filename)
        except FileNotFoundError:
            pass
        except PermissionError:
            logger.error(f"Permission denied while deleting an image: {filename}")
            logger.error(traceback.format_exc())
            pass
        except Exception as e:
            logger.error(f"An unexpected error occured while deleting an image: {e}")
            logger.error(traceback.format_exc())
            raise e

    def create_clothing(self, token: str, name: str, category: str, image_filename: str, color: Optional[str], seasons: Optional[list] = None, tags: Optional[list] = None, description: Optional[str] = None) -> Clothing:
        if not isinstance(name, str) or not name.strip():
            raise ClothingNameMissingError("The name is missing.")
        
        if not isinstance(category, str) or not category.strip():
            raise ClothingCategoryMissingError("The category is missing.")
        
        if not isinstance(image_filename, str) or not image_filename.strip():
            raise ClothingImageMissingError("The image filename is missing.")
        
        color_regex = r"^#([A-Fa-f0-9]{6})$"
        if isinstance(color, str) and not re_match(color_regex, color):
            raise ClothingColorMissingError("The color is missing or invalid. It should be a hex color code (e.g., #FFFFFF).")

        if not os.path.exists(os.path.join("app", "static", "temp", image_filename)):
            raise ClothingImageMissingError("The provided image file does not exist.")
        
        if category.upper() not in ClothingCategory.__members__:
            raise ClothingCategoryMissingError("The provided category is not valid. It should be one of the following: " + ", ".join(ClothingCategory.__members__.keys()))
        
        if len(name) < 3:
            raise ClothingNameTooShortError("The provided name is too short, it has to be at least 3 characters long.")
        
        if len(name) > 50:
            raise ClothingNameTooLongError("The provided name is too long, it has to be at most 50 characters long.")
            
        if isinstance(description, str) and len(description) > 255:
            raise ClothingDescriptionTooLongError("The provided description is too long, it has to be at most 255 characters long.")

        if isinstance(seasons, list) and all(isinstance(season, str) for season in seasons):
            for season in seasons:
                if str(season).upper() not in ClothingSeason.__members__:
                    raise ValueError(f"The provided season ({season}) is not valid. It should be one of the following: " + ", ".join(ClothingSeason.__members__.keys()))
        
            seasons = [ClothingSeason[season.upper()] for season in seasons]
        
        if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
            for tag in tags:
                if str(tag).upper() not in ClothingTags.__members__:
                    raise ValueError(f"The provided tag ({tag}) is not valid. It should be one of the following: " + ", ".join(ClothingTags.__members__.keys()))
        
            tags = [ClothingTags[tag.upper()] for tag in tags]

        user_id = authentication_manager.get_user_id_from_token(token)
        clothing_id = str(uuid.uuid4())

        clothing = Clothing(clothing_id, True, name, ClothingCategory[category], color, datetime.now(), user_id, image_filename, seasons, tags, description)

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO clothing(clothing_id, is_public, name, category, image, user_id, color, description) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (clothing.clothing_id, clothing.is_public, clothing.name, clothing.category.name, clothing.image, clothing.user_id, clothing.color, clothing.description))
                for season in clothing.seasons:
                    cursor.execute("INSERT INTO clothing_seasons(clothing_id, season) VALUES (%s, %s);", (clothing.clothing_id, season.name))
                for tag in clothing.tags:
                    cursor.execute("INSERT INTO clothing_tags(clothing_id, tag) VALUES (%s, %s);", (clothing.clothing_id, tag.name))
                conn.commit()

                image_manager.move_preview_image_to_permanent(image_filename)
        except IntegrityError as e:
            raise ClothingImageInvalidError("The provided image is already used by another clothing.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding a new clothing to the database: {e}")
            logger.error(traceback.format_exc())
            raise e

        return clothing

    def get_clothing_by_id(self, token: str, clothing_id: Optional[str]) -> Clothing:
        if not isinstance(clothing_id, str) or not clothing_id.strip():
            raise ClothingIDMissingError("The clothing ID is missing.")

        user_id = authentication_manager.get_user_id_from_token(token)
        
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT clothing_id, is_public, name, category, color, created_at, image, user_id, color, description FROM clothing WHERE clothing_id = %s;", (clothing_id,))
                clothing = cursor.fetchone()
                
                if clothing is None:
                    raise ClothingNotFoundError("The provided ID does not match any clothing in the database.")
                    
                if clothing[7] != user_id:
                    if not clothing[1]:
                        raise ClothingNotFoundError("The provided ID does not match any clothing in the database for the current user.")
                
                cursor.execute("SELECT season FROM clothing_seasons WHERE clothing_id = %s;", (clothing_id,))
                seasons = cursor.fetchall()
                
                cursor.execute("SELECT tag FROM clothing_tags WHERE clothing_id = %s;", (clothing_id,))
                tags = cursor.fetchall()
                
                clothing = Clothing(clothing[0], clothing[1], clothing[2], ClothingCategory[clothing[3]], clothing[4], clothing[5], datetime.fromisoformat(clothing[6]), clothing[7], clothing[8], [ClothingSeason[season[0]] for season in seasons],
                        [ClothingTags[tag[0]] for tag in tags], clothing[9])
        
        except ClothingNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving clothing by ID: {e}")
            logger.error(traceback.format_exc())
            raise e
        
        return clothing

    def get_list_of_clothing_by_user_id(self, token: str, user_id: Optional[str], limit: int = 1000, offset: int = 0) -> list[Clothing]:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ClothingIDMissingError("The provided user ID is missing or invalid.")

        user_id_from_token = authentication_manager.get_user_id_from_token(token)
        clothes_list: list[Clothing] = []

        statement = f"SELECT clothing_id, is_public, name, category, color, created_at, user_id, image, description FROM clothing WHERE user_id = %s ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};"
        params = (user_id, )
        
        if user_id != user_id_from_token:
            statement = f"SELECT clothing_id, is_public, name, category, color, created_at, user_id, image, description FROM clothing WHERE user_id = %s AND is_public = %s ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};"
            params = (user_id, True)
        
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute(statement, params)
                clothes = cursor.fetchall()

                for clothing in clothes:
                    clothing_id = clothing[0]
                    cursor.execute("SELECT season FROM clothing_seasons WHERE clothing_id = %s;", (clothing_id,))
                    seasons = cursor.fetchall()
                
                    cursor.execute("SELECT tag FROM clothing_tags WHERE clothing_id = %s;", (clothing_id,))
                    tags = cursor.fetchall()

                    clothes_list.append(Clothing(clothing[0], clothing[1], clothing[2], ClothingCategory[clothing[3]], clothing[4], clothing[5], datetime.fromisoformat(clothing[6]), clothing[7], clothing[8], [ClothingSeason[season[0]] for season in seasons],
                        [ClothingTags[tag[0]] for tag in tags], clothing[9]))
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving clothes for user {user_id}: {e}")
            logger.error(f"{traceback.format_exc()}")
            raise e
        
        return clothes_list
    
    """
    def updateClothing(self, token: str, clothingID: str, name: str | None, category: str | None, description: str | None, color: str | None, seasons: list | None, tags: list | None, image: str | None) -> Clothing:
        try:
            userID = authentication_manager.retrieveUserIDByToken(token)
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image, name, category, description, color FROM clothing WHERE clothing_id = %s AND user_id = %s;", (clothingID, userID,))
                clothing = cursor.fetchone()
                
                if clothing is None:
                    raise ClothingNotFoundError("The provided clothing ID does not match any clothing in the database.")
                
                if image is None:
                    image = clothing[0].split("/")[-1]
                
                if name is None:
                    name = clothing[1]
                
                if category is None:
                    category = clothing[2]
                    
                if description is None:
                    description = clothing[3]
                    
                if color is None:
                    color = clothing[4]
                    
                if name == "":
                    raise ClothingNameTooShortError("The provided name is too short.")
                
                if len(name) > 50:
                    raise ClothingNameTooLongError("The provided name is too long.")
                
                if description is not None and len(description) > 255:
                    raise ClothingDescriptionTooLongError("The provided description is too long.")
                
                if description == "":
                    description = None
                
                cursor.execute("UPDATE clothing SET name = %s, category = %s, description = %s, color = %s, image = %s WHERE clothing_id = %s AND user_id = %s;", (name, category, description, color, "/public/clothing_images/" + image, clothingID, userID,))
                
                if seasons is not None:
                    cursor.execute("DELETE FROM clothing_seasons WHERE clothing_id = %s;", (clothingID,))
                    for season in seasons:
                        cursor.execute("INSERT INTO clothing_seasons(clothing_id, season) VALUES (%s, %s);", (clothingID, season))
                
                if tags is not None:
                    cursor.execute("DELETE FROM clothing_tags WHERE clothing_id = %s;", (clothingID,))
                    for tag in tags:
                        cursor.execute("INSERT INTO clothing_tags(clothing_id, tag) VALUES (%s, %s);", (clothingID, tag))
                conn.commit()
                
            self.deleteImageIfNotUsed(clothing[0])
        except ClothingNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occured: {e}")
            logger.error(traceback.format_exc())
            raise e
        
        return self.getClothing(token, clothingID)
    """
    
    def delete_clothing_by_id(self, token: str, clothing_id: str) -> None:
        if not isinstance(clothing_id, str) or not clothing_id.strip():
            raise ClothingIDMissingError("The clothing ID is missing.")
        
        user_id = authentication_manager.get_user_id_from_token(token)
        
        try:    
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image FROM clothing WHERE clothing_id = %s AND user_id = %s;", (clothing_id, user_id,))
                image = cursor.fetchone()
                
                if image is None:
                    raise ClothingNotFoundError("The provided clothing ID does not match any clothing in the database.")
                
                cursor.execute("DELETE FROM clothing_tags WHERE clothing_id = %s;", (clothing_id,))
                cursor.execute("DELETE FROM clothing_seasons WHERE clothing_id = %s;", (clothing_id,))
                cursor.execute("DELETE FROM clothing WHERE clothing_id = %s AND user_id = %s;", (clothing_id, user_id,))
                conn.commit()
                
            self._delete_unused_image(image[0])
        except ClothingNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting clothing by ID: {e}")
            logger.error(traceback.format_exc())
            raise e
            
clothing_manager = ClothingManager()