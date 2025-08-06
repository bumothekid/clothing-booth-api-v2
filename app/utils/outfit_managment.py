__all__ = ["outfit_manager"]

import traceback
import uuid
from datetime import datetime
from app.utils.database import Database
from app.utils.exceptions import OutfitNotFoundError, OutfitNameTooShortError, OutfitNameTooLongError, OutfitDescriptionTooLongError, OutfitNameMissingError, OutfitClothingIDsMissingError, OutfitClothingIDInvalidError, OutfitSeasonsInvalidError, OutfitTagsInvalidError, OutfitIDMissingError, OutfitPermissionError, OutfitLimitInvalidError, OutfitOffsetInvalidError, OutfitValidationError
from typing import Optional
from mysql.connector.errors import IntegrityError
from app.models.outfit import Outfit, OutfitTags, OutfitSeason
from app.utils.authentication_managment import AuthenticationManager
from app.utils.logging import get_logger

logger = get_logger()

class OutfitManager:
    def ensure_table_exists(self) -> None:
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

    def create_outfit(self, token: str, name: str, clothing_ids: Optional[list[str]], seasons: Optional[list[str]], tags: Optional[list[str]], description: Optional[str] = None) -> Outfit:
        if not isinstance(name, str) or not name.strip():
            raise OutfitNameMissingError("The provided name is missing or invalid.")
        
        if len(name) < 3:
            raise OutfitNameTooShortError("The provided name is too short, it has to be at least 3 characters long.")

        if len(name) > 50:
            raise OutfitNameTooLongError("The provided name is too long, it has to be at most 50 characters long.")
        
        if not isinstance(clothing_ids, list):
            raise OutfitClothingIDsMissingError("The provided clothing ID(s) are missing or invalid.")

        if not isinstance(seasons, None):
            if not isinstance(seasons, list) or not all(isinstance(season, str) for season in seasons):
                raise OutfitSeasonsInvalidError("Seasons must be a list of strings.")
            
            for season in seasons:
                if season.strip().upper() not in OutfitSeason.__members__:
                    raise OutfitSeasonsInvalidError(f"The provided season ({season}) is not valid.")

            seasons = [OutfitSeason[season.strip().upper()] for season in seasons]

        if not isinstance(tags, None):
            if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                raise OutfitTagsInvalidError("Tags must be a list of strings.")

            for tag in tags:
                if tag.strip().upper() not in OutfitTags.__members__:
                    raise OutfitTagsInvalidError(f"The provided tag ({tag}) is not valid.")

            tags = [OutfitTags[tag.strip().upper()] for tag in tags]

        if isinstance(description, str) and len(description) > 255:
            raise OutfitDescriptionTooLongError("The provided description is too long, it has to be at most 255 characters long.")

        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)
        outfit_id = str(uuid.uuid4())
        
        valid_clothing_ids = []
        for clothing_id in set(clothing_ids):
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT clothing_id FROM clothing WHERE clothing_id = %s AND user_id = %s;", (clothing_id, user_id))
                if cursor.fetchone() is None:
                    raise OutfitClothingIDInvalidError(f"The provided clothing ID ({clothing_id}) is invalid or does not belong to the user.")

            valid_clothing_ids.append(clothing_id)

        outfit = Outfit(outfit_id, True, name, datetime.now(), user_id, valid_clothing_ids, seasons, tags, description)

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
    
    def get_outfit_by_id(self, token: str, outfit_id: Optional[str]) -> Outfit:
        if not isinstance(outfit_id, str) or not outfit_id.strip():
            raise OutfitIDMissingError("The provided outfit ID is missing or invalid.")
        
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
                        raise OutfitPermissionError("The provided ID does not match any public outfit in the database.")
                    
                cursor.execute("SELECT season FROM outfit_seasons WHERE outfit_id = %s;", (outfit_id,))
                seasons = cursor.fetchall()
                    
                cursor.execute("SELECT tag FROM outfit_tags WHERE outfit_id = %s;", (outfit_id,))
                tags = cursor.fetchall()
                    
                cursor.execute("SELECT clothing_id FROM outfit_clothing WHERE outfit_id = %s;", (outfit_id,))
                clothing_list = cursor.fetchall()

                outfit = Outfit(outfit[0], outfit[1], outfit[2], outfit[3], outfit[4], [clothing_id[0] for clothing_id in clothing_list], [OutfitSeason[season[0]] for season in seasons], [OutfitTags[tag[0]] for tag in tags], outfit[5])
        except OutfitNotFoundError as e:
            raise e
        except OutfitPermissionError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving outfit with ID {outfit_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

        return outfit

    def get_list_of_outfits_by_user_id(self, token: str, user_id: Optional[str], limit: int = 1000, offset: int = 0) -> list[Outfit]:
        if not isinstance(user_id, str) or not user_id.strip():
            raise OutfitIDMissingError("The provided user ID is missing or invalid.")
        
        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise OutfitLimitInvalidError("The limit must be a positive integer and cannot exceed 1000.")

        if not isinstance(offset, int) or offset < 0:
            raise OutfitOffsetInvalidError("The offset must be a positive integer.")

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
                    
                    outfit_instance = Outfit(outfit[0], outfit[1], outfit[2], outfit[3], outfit[4], [clothing_id[0] for clothing_id in clothing_list], [OutfitSeason[season[0]] for season in seasons], [OutfitTags[tag[0]] for tag in tags], outfit[5])
                    outfit_list.append(outfit_instance)
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving outfits for user {user_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

        return outfit_list
        
    def update_outfit(self, token: str, outfit_id: str, name: Optional[str] = None, is_public: Optional[bool] = None, seasons: Optional[list[str]] = None, tags: Optional[list[str]] = None, clothing_ids: Optional[list[str]] = None, description: Optional[str] = None) -> Outfit:
        user_id = AuthenticationManager.getInstance().get_user_id_from_token(token)
        
        fields = []
        values = []

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT outfit_id, is_public, name, created_at, user_id, description FROM outfit WHERE outfit_id = %s AND user_id = %s;", (outfit_id, user_id))
                result = cursor.fetchone()

                if result is None:
                    raise OutfitNotFoundError("The provided ID does not match any outfit in the database for the current user.")

                if isinstance(name, str):
                    if len(name) < 3:
                        raise OutfitNameTooShortError("The provided name is too short, it has to be at least 3 characters long.")
                    
                    if len(name) > 50:
                        raise OutfitNameTooLongError("The provided name is too long, it has to be at most 50 characters long.")
                    
                    if name != result[2]:
                        fields.append("name = %s")
                        values.append(name)

                if is_public is not None and is_public != result[1]:
                    fields.append("is_public = %s")
                    values.append(is_public)

                if description is not None and description != result[5]:
                    if len(description) > 255:
                        raise OutfitDescriptionTooLongError("The provided description is too long.")
                    
                    fields.append("description = %s")
                    values.append(description)

                if fields:
                    cursor.execute(f"UPDATE outfit SET {', '.join(fields)} WHERE outfit_id = %s;", (*values, outfit_id))

                cursor.execute("SELECT season FROM outfit_seasons WHERE outfit_id = %s;", (outfit_id,))
                existing_seasons: list[str] = [season[0] for season in cursor.fetchall()]

                if seasons is not None and seasons != existing_seasons:
                    new_seasons = [season for season in seasons if season not in existing_seasons]
                    old_seasons = [season for season in existing_seasons if season not in seasons]
                    
                    if old_seasons:
                        cursor.execute("DELETE FROM outfit_seasons WHERE outfit_id = %s AND season IN %s;", (outfit_id, tuple(old_seasons)))

                    if new_seasons:
                        for season in new_seasons:
                            if season.strip().upper() not in OutfitSeason.__members__:
                                raise OutfitSeasonsInvalidError(f"The provided season ({season}) is not valid.")

                            cursor.execute("INSERT INTO outfit_seasons(outfit_id, season) VALUES (%s, %s);", (outfit_id, season.strip().upper()))

                cursor.execute("SELECT tag FROM outfit_tags WHERE outfit_id = %s;", (outfit_id,))
                existing_tags: list[str] = [tag[0] for tag in cursor.fetchall()]

                if tags is not None and tags != existing_tags:
                    new_tags = [tag for tag in tags if tag not in existing_tags]
                    old_tags = [tag for tag in existing_tags if tag not in tags]
                    
                    if old_tags:
                        cursor.execute("DELETE FROM outfit_tags WHERE outfit_id = %s AND tag IN %s;", (outfit_id, tuple(old_tags)))

                    if new_tags:
                        for tag in new_tags:
                            if tag.strip().upper() not in OutfitTags.__members__:
                                raise OutfitTagsInvalidError(f"The provided tag ({tag}) is not valid.")

                            cursor.execute("INSERT INTO outfit_tags(outfit_id, tag) VALUES (%s, %s);", (outfit_id, tag.strip().upper()))

                cursor.execute("SELECT clothing_id FROM outfit_clothing WHERE outfit_id = %s;", (outfit_id,))
                existing_clothing_ids: list[str] = [clothing_id[0] for clothing_id in cursor.fetchall()]

                if clothing_ids is not None and clothing_ids != existing_clothing_ids:
                    new_clothing_ids = [clothing_id for clothing_id in clothing_ids if clothing_id not in existing_clothing_ids]
                    old_clothing_ids = [clothing_id for clothing_id in existing_clothing_ids if clothing_id not in clothing_ids]
                    
                    if old_clothing_ids:
                        cursor.execute("DELETE FROM outfit_clothing WHERE outfit_id = %s AND clothing_id IN %s;", (outfit_id, tuple(old_clothing_ids)))

                    if new_clothing_ids:
                        for clothing_id in new_clothing_ids:
                            cursor.execute("INSERT INTO outfit_clothing(outfit_id, clothing_id) VALUES (%s, %s);", (outfit_id, clothing_id))
                            
                conn.commit()
        except (OutfitValidationError) as e:
            raise e
        except IntegrityError as e:
            raise OutfitClothingIDInvalidError(f"The provided clothing ID(s) are invalid or do not belong to the user: {e}")
        except OutfitNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating outfit with ID {outfit_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

    def delete_outfit_by_id(self, token: str, outfit_id: Optional[str]) -> None:
        if not isinstance(outfit_id, str) or not outfit_id.strip():
            raise OutfitIDMissingError("The provided outfit ID is missing or invalid.")
        
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
        return None
    
    
outfit_manager = OutfitManager()
