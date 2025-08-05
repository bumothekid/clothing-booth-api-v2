import random
import base64
import jwt
from os import getenv
from typing import Optional
from string import ascii_letters, digits
import traceback
from datetime import datetime, timedelta
from flask import request, jsonify
from app.utils.database import Database
from app.utils.exceptions import AuthValidationError, AuthTokenExpiredError, AuthAccessTokenInvalidError, AuthRefreshTokenInvalidError, AuthAccessTokenMissingError, AuthRefreshTokenMissingError, AuthUserIDMissingError
from app.utils.logging import Logger

SECRET_TOKEN_KEY = getenv("SECRET_TOKEN_KEY")
ACCESS_TOKEN_EXPIRY_HOURS = 1
REFRESH_TOKEN_EXPIRY_DAYS = 90
TOKEN_LENGTH = 16

logger = Logger.getLogger()

def authorize_request(f):
    def wrapper(*args, **kwargs):
        if "Authorization" not in request.headers:
            return jsonify({"error": "No token provided"}), 401
        
        token = request.headers["Authorization"]
        if not AuthenticationManager.getInstance()._verify_access_token(token):
            return jsonify({"message": "Unauthorized access"}), 403
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

class AuthenticationManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthenticationManager, cls).__new__(cls)
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
            cursor.execute("""CREATE TABLE IF NOT EXISTS refresh_tokens(
                           user_id VARCHAR(36) NOT NULL,
                           refresh_token VARCHAR(24) PRIMARY KEY,
                           refresh_token_expiry TIMESTAMP DEFAULT NULL,
                           FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                           );
                           """)
            conn.commit()

    def generate_token_pair(self, user_id: Optional[str], is_guest: Optional[bool]) -> tuple:
        if not isinstance(user_id, str) or not user_id.strip():
            raise AuthUserIDMissingError("The user_id is missing or invalid.")
        
        if not isinstance(is_guest, bool):
            raise ValueError("The is_guest parameter must be a boolean value.")

        try:
            refresh_token = self._generate_refresh_token()
            refreshTokenExpiry = (datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
            
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                if not is_guest:
                    cursor.execute("INSERT INTO refresh_tokens(user_id, refresh_token, refresh_token_expiry) VALUES (%s, %s, %s);", (user_id, refresh_token, refreshTokenExpiry))
                else:
                    cursor.execute("INSERT INTO refresh_tokens(user_id, refresh_token) VALUES(%s, %s);", (user_id, refresh_token))
                    
                conn.commit()

            access_token = self._generate_access_token(user_id, is_guest=is_guest)

            return access_token, ACCESS_TOKEN_EXPIRY_HOURS * 60 * 60, refresh_token
        except Exception as e:
            logger.error(f"An unexpected error occurred while generating a new token pair: {e}")
            logger.error(traceback.format_exc())
            raise

    def refresh_access_token(self, old_access_token: Optional[str], refresh_token:  Optional[str]) -> tuple:
        if not isinstance(old_access_token, str) or not old_access_token.strip():
            raise AuthAccessTokenMissingError("The access_token is missing.")
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise AuthRefreshTokenMissingError("The refresh_token is missing.")

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM refresh_tokens WHERE refresh_token = %s;", (refresh_token,))
                user_id = cursor.fetchone()

                if not user_id:
                    raise AuthRefreshTokenInvalidError("The provided refresh token is invalid.")

                user_id = user_id[0]

                is_guest = self._get_payload_from_access_token(old_access_token).get('is_guest', False)
                access_token = self._generate_access_token(user_id, is_guest=is_guest)
                new_refresh_token = self._generate_refresh_token()

                if is_guest:
                    cursor.execute("""
                                UPDATE refresh_tokens
                                SET refresh_token = %s
                                WHERE refresh_token = %s;
                                """, (new_refresh_token, refresh_token,))
                else:
                    refresh_token_expiry = (datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("""
                                    UPDATE refresh_tokens
                                    SET refresh_token_expiry = %s, refresh_token = %s
                                    WHERE refresh_token = %s;
                                    """, (refresh_token_expiry, new_refresh_token, refresh_token,))
                    
                conn.commit()

            return access_token, ACCESS_TOKEN_EXPIRY_HOURS * 60 * 60, new_refresh_token
        except AuthValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while refreshing an access token: {e}")
            logger.error(traceback.format_exc())
            raise e
            
    def delete_refresh_token(self, refresh_token: Optional[str]) -> None:
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise AuthRefreshTokenMissingError("The refresh_token is missing or invalid.")

        try:
            with Database.getConnection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM refresh_tokens WHERE refresh_token = %s;", (refresh_token,))
                if cursor.rowcount < 1:
                    raise AuthRefreshTokenInvalidError("The provided refresh token is invalid.")

                conn.commit()
        except AuthValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting a refresh token: {e}")
            logger.error(traceback.format_exc())
            raise e

    def get_user_id_from_token(self, token: str) -> str:
        if not isinstance(token, str) or not token.strip():
            raise AuthAccessTokenMissingError("The access_token is missing or invalid.")
        
        try:
            payload = self._get_payload_from_access_token(token)
            return payload.get('sub')
        except AuthValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting user ID from token: {e}")
            logger.error(traceback.format_exc())
            raise e
        
    def _verify_access_token(self, token: str) -> bool:
        try:
            jwt.decode(token, SECRET_TOKEN_KEY, algorithms=['HS256'])
            return True
        except:
            return False
        
    def _get_payload_from_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_TOKEN_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthTokenExpiredError("The provided access token has expired.")
        except jwt.InvalidTokenError:
            raise AuthAccessTokenInvalidError("The provided access token is invalid.")

    def _generate_refresh_token(self) -> str:
        randRefreshToken = "".join(random.choices(ascii_letters + digits, k=TOKEN_LENGTH))
        randRefreshTokenb64 = base64.b64encode(randRefreshToken.encode()).decode()
        return f"{randRefreshTokenb64}"

    def _generate_access_token(self, user_id: str, is_guest: bool) -> str:
        payload = {
            'sub': user_id,
            'exp': datetime.now() + timedelta(hours=ACCESS_TOKEN_EXPIRY_HOURS),
            'is_guest': is_guest
        }
        return jwt.encode(payload, SECRET_TOKEN_KEY, algorithm='HS256')