import traceback
import uuid
from datetime import datetime
from app.utils.database import Database
from app.utils.exceptions import OutfitNotFoundError, OutfitNameTooShortError, OutfitNameTooLongError, OutfitDescriptionTooLongError
from werkzeug.datastructures import FileStorage
from PIL import Image
from typing import Optional
from mysql.connector.errors import IntegrityError
from backgroundremover.bg import remove
from app.models.outfit import Outfit, OutfitTags, OutfitSeason
from app.utils.authentication_managment import AuthenticationManager
from app.utils.logging import Logger
from app.utils.image_managment import ImageManager
import os

logger = Logger.getLogger()

class OutfitManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OutfitManager, cls).__new__(cls)
            cls._instance._checkTable()
        return cls._instance
    
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _checkTable(self) -> None:
        with Database.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS outfit(
                            outfit_id VARCHAR(36) PRIMARY KEY,
                            is_public BOOLEAN DEFAULT TRUE,
                            name VARCHAR(50) NOT NULL,
                            is_favorite BOOLEAN DEFAULT FALSE,
                            user_id VARCHAR(36) NOT NULL,
                            description VARCHAR(255) DEFAULT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                            );
                            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS outfit_seasons(
                            outfit_id VARCHAR(36) NOT NULL,
                            season ENUM('SPRING', 'SUMMER', 'AUTUMN', 'WINTER') NOT NULL,
                            FOREIGN KEY (outfit_id) REFERENCES outfit(outfit_id) ON DELETE CASCADE
                            );
                            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS outfit_tags(
                            outfit_id VARCHAR(36) NOT NULL,
                            tag VARCHAR(50) NOT NULL,
                            FOREIGN KEY (outfit_id) REFERENCES outfit(outfit_id) ON DELETE CASCADE
                            );
                            """)
            cursor.execute("""
                            CREATE TABLE IF NOT EXISTS outfit_clothing(
                            outfit_id VARCHAR(36) NOT NULL,
                            clothing_id VARCHAR(36) NOT NULL,
                            FOREIGN KEY (outfit_id) REFERENCES outfit(outfit_id) ON DELETE CASCADE,
                            FOREIGN KEY (clothing_id) REFERENCES clothing(clothing_id) ON DELETE CASCADE
                            );
                            """)
            conn.commit()

    def create_outfit(self, token: str, name: str, seasons: list[str], tags: list[str], clothing_ids: list[str], description: Optional[str] = None) -> Outfit:
        if name == "":
            raise OutfitNameTooShortError("The provided name is too short.")

        if len(name) > 50:
            raise OutfitNameTooLongError("The provided name is too long.")
        
        if len(description) > 255:
            raise OutfitDescriptionTooLongError("The provided description is too long.")

        if description == "":
            description = None

        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)
        outfit_id = str(uuid.uuid4())
        
        valid_clothing_ids = []
        for clothing_id in clothing_ids:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT clothing_id FROM clothing WHERE clothing_id = %s AND user_id = %s;", (clothing_id, user_id))
                if cursor.fetchone() is None:
                    logger.warning(f"Clothing with ID {clothing_id} not found or does not belong to the user.")
                    #raise ClothingNotFoundError(f"Clothing with ID {clothing_id} not found or does not belong to the user.")
                    continue
            valid_clothing_ids.append(clothing_id)

        outfit = Outfit(outfit_id, True, name, [OutfitSeason[season] for season in seasons], [OutfitTags[tag] for tag in tags], datetime.now(), user_id, valid_clothing_ids, description)

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO outfit(outfit_id, is_public, name, user_id, description) VALUES (%s, %s, %s, %s, %s);", (outfit.outfit_id, outfit.is_public, outfit.name, outfit.user_id, outfit.description))
                for season in outfit.seasons:
                    cursor.execute("INSERT INTO outfit_seasons(outfit_id, season) VALUES (%s, %s);", (outfit.outfit_id, season.name))
                for tag in outfit.tags:
                    cursor.execute("INSERT INTO outfit_tags(outfit_id, tag) VALUES (%s, %s);", (outfit.outfit_id, tag.name))
                for clothing_id in outfit.clothing_ids:
                    cursor.execute("INSERT INTO outfit_clothing(outfit_id, clothing_id) VALUES (%s, %s);", (outfit.outfit_id, clothing_id))
                conn.commit()
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding a new outfit to the database: {e}")
            logger.error(traceback.format_exc())
            raise e

        return outfit
    
    def get_outfit_by_id(self, outfit_id: str, token) -> Outfit:
        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)
        
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT outfit_id, is_public, name, created_at, user_id, description FROM outfit WHERE outfit_id = %s", (outfit_id, ))
                outfit = cursor.fetchone()
                
                if outfit is None:
                        raise OutfitNotFoundError("The provided ID does not match any outfit in the database.")
                        
                if outfit[4] != user_id:
                    if not outfit[1]:
                        raise OutfitNotFoundError("The provided ID does not match any outfit in the database for the current user.")
                    
                cursor.execute("SELECT season FROM outfit_seasons WHERE outfit_id = %s;", (outfit_id,))
                seasons = cursor.fetchall()
                    
                cursor.execute("SELECT tag FROM outfit_tags WHERE outfit_id = %s;", (outfit_id,))
                tags = cursor.fetchall()
                    
                cursor.execute("SELECT clothing_id FROM outfit_clothing WHERE outfit_id = %s;", (outfit_id,))
                clothing_list = cursor.fetchall()
                
                outfit = Outfit(outfit[0], outfit[1], outfit[2], [OutfitSeason[season[0]] for season in seasons], [OutfitTags[tag[0]] for tag in tags], outfit[3], outfit[4], [clothing_id[0] for clothing_id in clothing_list], outfit[5])
        except OutfitNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving outfit with ID {outfit_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

        return outfit

    def get_list_of_outfits_by_user_id(self, user_id: str, token: str, limit: int = 18446744073709551615, offset: int = 0) -> list[Outfit]:
        user_id_from_token = AuthenticationManager.getInstance().get_user_id_from_token(token)
        
        outfit_list: list[Outfit] = []

        statement = f"SELECT outfit_id, is_public, name, is_favorite, user_id, description, created_at FROM clothing WHERE user_id = %s ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};"
        params = (user_id, )
        
        if user_id != user_id_from_token:
            statement = f"SELECT outfit_id, is_public, name, created_at, user_id, description FROM clothing WHERE user_id = %s AND is_public = %s ORDER BY created_at DESC LIMIT {limit} OFFSET {offset};"
            params = (user_id, True, )
        
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute(statement, params)

                outfits = cursor.fetchall()
                
                for outfit in outfits:
                    cursor.execute("SELECT season FROM outfit_seasons WHERE outfit_id = %s;", (outfit[0],))
                    seasons = cursor.fetchall()
                    
                    cursor.execute("SELECT tag FROM outfit_tags WHERE outfit_id = %s;", (outfit[0],))
                    tags = cursor.fetchall()
                    
                    cursor.execute("SELECT clothing_id FROM outfit_clothing WHERE outfit_id = %s;", (outfit[0],))
                    clothing_list = cursor.fetchall()
                    
                    outfit_instance = Outfit(outfit[0], outfit[1], outfit[2], [OutfitSeason[season[0]] for season in seasons], [OutfitTags[tag[0]] for tag in tags], outfit[3], outfit[4], [clothing_id[0] for clothing_id in clothing_list], outfit[5])
                    outfit_list.append(outfit_instance)
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving outfits for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

        return outfit_list
        
    def update_outfit(self, token: str, outfit_id: str, name: Optional[str] = None, is_public: Optional[bool] = None, seasons: Optional[list[str]] = None, tags: Optional[list[str]] = None, clothing_ids: Optional[list[str]] = None, description: Optional[str] = None) -> Outfit:
        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT outfit_id, is_public, name, created_at, user_id, description FROM outfit WHERE outfit_id = %s AND user_id = %s;", (outfit_id, user_id))
                result = cursor.fetchone()

                if result is None:
                    raise OutfitNotFoundError("The provided ID does not match any outfit in the database for the current user.")

                if name is not None and name != result[2]:
                    if len(name) < 1:
                        raise OutfitNameTooShortError("The provided name is too short.")
                    if len(name) > 50:
                        raise OutfitNameTooLongError("The provided name is too long.")
                    cursor.execute("UPDATE outfit SET name = %s WHERE outfit_id = %s;", (name, outfit_id))

                if is_public is not None and is_public != result[1]:
                    cursor.execute("UPDATE outfit SET is_public = %s WHERE outfit_id = %s;", (is_public, outfit_id))

                if description is not None and description != result[5]:
                    if len(description) > 255:
                        raise OutfitDescriptionTooLongError("The provided description is too long.")
                    cursor.execute("UPDATE outfit SET description = %s WHERE outfit_id = %s;", (description, outfit_id))
                    
                cursor.execute("SELECT season FROM outfit_seasons WHERE outfit_id = %s;", (outfit_id,))
                existing_seasons: list[str] = [season[0] for season in cursor.fetchall()]

                if seasons is not None and seasons != existing_seasons:
                    new_seasons = [season for season in seasons if season not in existing_seasons]
                    old_seasons = [season for season in existing_seasons if season not in seasons]
                    
                    if old_seasons:
                        cursor.execute("DELETE FROM outfit_seasons WHERE outfit_id = %s AND season IN %s;", (outfit_id, tuple(old_seasons)))
                        
                    if new_seasons:
                        for season in new_seasons:
                            if season not in OutfitSeason.__members__:
                                raise ValueError(f"The provided season ({season}) is not valid.")
                            cursor.execute("INSERT INTO outfit_seasons(outfit_id, season) VALUES (%s, %s);", (outfit_id, season))
                    for season in seasons:
                        if season.strip().upper() not in OutfitSeason.__members__:
                            raise ValueError(f"The provided season ({season}) is not valid.")
                        cursor.execute("INSERT INTO outfit_seasons(outfit_id, season) VALUES (%s, %s);", (outfit_id, season.strip().upper()))

                if tags is not None:
                    cursor.execute("DELETE FROM outfit_tags WHERE outfit_id = %s;", (outfit_id,))
                    for tag in tags:
                        if tag.strip().upper() not in OutfitTags.__members__:
                            raise ValueError(f"The provided tag ({tag}) is not valid.")
                        cursor.execute("INSERT INTO outfit_tags(outfit_id, tag) VALUES (%s, %s);", (outfit_id, tag.strip().upper()))

                if clothing_ids is not None:
                    cursor.execute("DELETE FROM outfit_clothing WHERE outfit_id = %s;", (outfit_id,))
                    for clothing_id in clothing_ids:
                        cursor.execute("INSERT INTO outfit_clothing(outfit_id, clothing_id) VALUES (%s, %s);", (outfit_id, clothing_id))
                conn.commit()
        except (OutfitNameTooShortError, OutfitNameTooLongError, OutfitDescriptionTooLongError, ValueError) as e:
            logger.error(f"Error updating outfit: {e}")
            raise e

    def delete_outfit_by_id(self, token: str, outfit_id: str) -> None:
        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM outfit WHERE outfit_id = %s AND user_id = %s;", (outfit_id, user_id))
                result = cursor.fetchone()

                if result is None:
                    raise OutfitNotFoundError("The provided ID does not match any outfit in the database for the current user.")

                cursor.execute("DELETE FROM outfit_seasons WHERE outfit_id = %s;", (outfit_id,))
                cursor.execute("DELETE FROM outfit_tags WHERE outfit_id = %s;", (outfit_id,))
                cursor.execute("DELETE FROM outfit_clothing WHERE outfit_id = %s;", (outfit_id,))
                cursor.execute("DELETE FROM outfit WHERE outfit_id = %s;", (outfit_id,))
                conn.commit()
        except OutfitNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting outfit with ID {outfit_id}: {e}")
            logger.error(traceback.format_exc())
            raise e
