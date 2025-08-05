import random
import traceback
import uuid
import os
from app.utils.database import Database
from app.utils.exceptions import EmailAlreadyInUseError, UnsupportedFileTypeError, UserNotFoundError, UserProfilePictureNotFoundError, UsernameAlreadyInUseError, UsernameTooShortError, UsernameTooLongError, EmailInvalidError, PasswordTooShortError, WrongSignInCredentialsError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.utils.authentication_managment import AuthenticationManager
from werkzeug.datastructures import FileStorage
from mysql.connector.errors import IntegrityError
from PIL import Image
from os import path, remove
from app.models.user import PrivateUser, PublicUser
import re
from app.utils.logging import Logger

logger = Logger.getLogger()
        
class UserManagment:
    _instance = None
    
    def __new__(cls):
            if cls._instance is None:
                cls._instance = super(UserManagment, cls).__new__(cls)
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
                           CREATE TABLE IF NOT EXISTS users(
                           user_id VARCHAR(36) PRIMARY KEY,
                           is_guest BOOLEAN DEFAULT TRUE,
                           username VARCHAR(32) UNIQUE DEFAULT NULL,
                           email VARCHAR(255) UNIQUE DEFAULT NULL,
                           password VARCHAR(97) DEFAULT NULL,
                           profile_picture VARCHAR(255) UNIQUE DEFAULT NULL,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                           );
                           """)
            conn.commit()
    
    def _hashPassword(self, password: str) -> str:
        return PasswordHasher().hash(password)
    
    def _getSignInDetails(self, username: str = None, email: str = None) -> tuple:
        if username:
            return username.lower(), "username"
        elif email:
            return email.lower(), "email"
        else:
            raise ValueError("Either username or email must be provided.")
        
    def loginWithCredentials(self, password, username: str = None, email: str = None) -> tuple:
        try:
            signInName, signInCheck = self._getSignInDetails(username, email)
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                if signInCheck == "username":
                    cursor.execute("SELECT password, user_id FROM users WHERE username = %s;", (signInName, ))
                else:
                    cursor.execute("SELECT password, user_id FROM users WHERE email = %s;", (signInName, ))
                user = cursor.fetchone()
            
                if not user:
                    raise WrongSignInCredentialsError("The provided sign in credentials are wrong.")
                
                userPassword, userID = user
                
                try:
                    PasswordHasher().verify(userPassword, password)
                except VerifyMismatchError:
                    raise WrongSignInCredentialsError("The provided sign in credentials are wrong.")
        except WrongSignInCredentialsError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while signing in the user: {e}")
            logger.error(traceback.format_exc())
            raise e
        
        return AuthenticationManager.getInstance().generate_token_pair(userID)

    def register_guest(self) -> tuple:
        try:
            user_id = self._create_user()

            return AuthenticationManager.getInstance().generate_token_pair(user_id, is_guest=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while registering guest: {e}")
            raise

    def _create_user(self, is_guest: bool = True, email: str = None, username: str = None, password: str = None, profilePicture: str = None) -> str:
        user_id = str(uuid.uuid4())

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users(user_id, is_guest, email, username, password, profile_picture) VALUES (%s, %s, %s, %s, %s, %s);", (user_id, is_guest, email, username, password, profilePicture))
                conn.commit()
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating user: {e}")
            logger.error(traceback.format_exc())
            
            
        return user_id
    
    def registerNewUser(self, email: str, username: str, password: str, profilePicture: str) -> tuple:
        try:
            email = email.lower()
            
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise EmailInvalidError("The provided email is invalid.")
            
            if len(password) < 8:
                raise PasswordTooShortError("The provided password is too short.")
            
            if len(username) < 3:
                raise UsernameTooShortError("The provided username is too short.")
            
            if len(username) > 32:
                raise UsernameTooLongError("The provided username is too long.")
            
            if profilePicture not in os.listdir("app/static/profile_pictures/default/"):
                raise UserProfilePictureNotFoundError("The provided profile picture is not found in the default directory.")
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                
                hashedPassword = self._hashPassword(password)
                
                userID = str(uuid.uuid4())
                cursor.execute("INSERT INTO users(user_id, email, username, password, profile_picture) VALUES (%s, %s,  %s, %s, %s);", (userID, email, username, hashedPassword, "/public/profile_pictures/default/" + profilePicture))
                conn.commit()
                
                return AuthenticationManager.getInstance().generate_token_pair(userID)
        except IntegrityError as e:
            if "email" in e.msg:
                raise EmailAlreadyInUseError("The provided 'email' is already in use.")
            elif "username" in e.msg:
                raise UsernameAlreadyInUseError("The provided 'username' is already in use.")
            else:
                raise Exception(e.msg)
        except Exception as e:
            logger.error(f"An unexpected error occurred while signing up the user: {e}")
            logger.error(traceback.format_exc())
            raise e
        
    def deleteAccount(self, token: str, password: str) -> None:
        try:
            userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password FROM users WHERE user_id = %s;", (userID, ))
                userPassword = cursor.fetchone()[0]
                
                try:
                    PasswordHasher().verify(userPassword, password)
                except VerifyMismatchError:
                    raise WrongSignInCredentialsError("The provided sign in credentials are wrong.")
                
                cursor.execute("DELETE FROM users WHERE user_id = %s;", (userID, ))
                conn.commit()
        except WrongSignInCredentialsError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting the user: {e}")
            logger.error(traceback.format_exc())
            raise e
    
    def setUsername(self, username: str, token: str) -> tuple:
        try:
            username = username.lower().strip()
            
            if len(username) < 3:
                raise UsernameTooShortError("The provided username is too short.")
            
            if len(username) > 32:
                raise UsernameTooLongError("The provided username is too long.")
            
            userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE user_id = %s;", (userID, ))
                oldUsername = cursor.fetchone()
                cursor.execute("UPDATE users SET username = %s WHERE user_id = %s;", (username, userID, ))
                conn.commit()
                
            return username, oldUsername if oldUsername is None else oldUsername[0]
        except IntegrityError as e:
            if "username" in e.msg:
                raise UsernameAlreadyInUseError("The provided 'username' is already in use.")
            raise Exception(e.msg)
        except Exception as e:
            logger.error(f"An unexpected error occurred while setting the username: {e}")
            logger.error(traceback.format_exc())
            raise e
            
        
    def getMyUser(self, token: str) -> PrivateUser:
        try:
            userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, created_at, updated_at, email, profile_picture FROM users WHERE user_id = %s;", (userID, ))
                user = cursor.fetchone()
            
            return PrivateUser(*user)
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving the user: {e}")
            logger.error(traceback.format_exc())
            raise e
    
    def getUserByUserID(self, userID: str) -> PublicUser:
        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, created_at FROM users WHERE user_id = %s;", (userID, ))
                user = cursor.fetchone()
            
            if not user:
                raise UserNotFoundError("The provided user_id is not associated with any users.")
            
            return PublicUser(*user)
        except UserNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while retrieving the user: {e}")
            logger.error(traceback.format_exc())
            raise e
        
    def getUserProfilePicture(self, userID: str) -> str:
        if not path.exists(f"static/profile_pictures/{userID}.webp"):
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT profile_picture FROM users WHERE user_id = %s;", (userID, ))
                profilePicture = cursor.fetchone()
                
                if not profilePicture:
                    raise UserNotFoundError("The provided user_id is not associated with any users.")
                
                return profilePicture[0]
        
        return f"/public/profile_pictures/{userID}.webp"
    
    def setProfilePicture(self, file: FileStorage, token: str) -> PrivateUser:
        fileExtension = file.filename.split(".")[-1].lower()
        
        if fileExtension not in ["jpg", "jpeg", "png"]:
            raise UnsupportedFileTypeError("The provided file type is not supported.")
        
        userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
        
        try:
            image = Image.open(file.stream)
            image.thumbnail((300, 300))
            image.save(f"app/static/profile_pictures/{userID}.webp", optimize=True, quality=95, format="webp")
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET profile_picture = %s WHERE user_id = %s;", (f"/public/profile_pictures/{userID}.webp", userID))
                conn.commit()
        except Exception as e:
            logger.error(f"An unexpected error occurred while setting the profile picture: {e}")
            logger.error(traceback.format_exc())
            raise e
        
        return self.getMyUser(token)
    
    def setDefaultProfilePicture(self, profilePicture: str, token: str) -> PrivateUser:
        userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
        
        if profilePicture not in os.listdir("app/static/profile_pictures/default/"):
            raise UserProfilePictureNotFoundError("The provided profile picture is available. Please choose one of the following: " + ", ".join(os.listdir("app/static/profile_pictures/default/")))
        
        with Database.getConnection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET profile_picture = %s WHERE user_id = %s;", ("/public/profile_pictures/default/" + profilePicture, userID))
            conn.commit()
        
        return self.getMyUser(token)
    
    def removeProfilePicture(self, token: str) -> None:
        try:
            userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
            
            if not path.exists(f"app/static/profile_pictures/{userID}.webp"):
                raise UserProfilePictureNotFoundError("The user profile picture is not set.")
        
            remove(f"app/static/profile_pictures/{userID}.webp")
            
            profilePictures = os.listdir("app/static/profile_pictures/default/")
            profilePicture = f"/public/profile_pictures/default/{random.choice(profilePictures)}"
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET profile_picture = %s WHERE user_id = %s;", (profilePicture, userID, ))
                conn.commit()
        except UserProfilePictureNotFoundError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while removing the profile picture: {e}")
            logger.error(traceback.format_exc())
            raise e
    
    def getMyProfilePicture(self, token: str) -> str:
        userID = AuthenticationManager.getInstance().retrieveUserIDByToken(token)
        
        if not path.exists(f"app/static/profile_pictures/{userID}.webp"):
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT profile_picture FROM users WHERE user_id = %s;", (userID, ))
                profilePicture = cursor.fetchone()[0]
                
                return profilePicture
        
        return f"/public/profile_pictures/{userID}.webp"