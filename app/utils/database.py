from sys import exit
from mysql.connector import pooling, MySQLConnection
from app.utils.logging import get_logger
from os import getenv

logger = get_logger()

class Database:
    _pool: pooling.MySQLConnectionPool = None
    
    @classmethod
    def getConnection(cls) -> MySQLConnection:
        if cls._pool is None:
            
            
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="connectionPool",
                    pool_size=5,
                    host=getenv("DATABASE_HOST", "localhost"),
                    port=getenv("DATABASE_PORT", "3306"),
                    user=getenv("DATABASE_USERNAME"),
                    password=getenv("DATABASE_PASSWORD"),
                    database=getenv("DATABASE_NAME")
                )
                
                connection = cls._pool.get_connection()
                connection.ping()
                connection.close()
                
                logger.debug(f"Successfully created database connection pool.")
            except Exception as e:
                logger.critical(f"Failed to create database connection pool: {e}")
                exit(1)

        return cls._pool.get_connection()