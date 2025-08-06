from mysql.connector import pooling, MySQLConnection
from dotenv import load_dotenv
from os import getenv

class Database:
    _pool: pooling.MySQLConnectionPool = None
    
    @classmethod
    def getConnection(cls) -> MySQLConnection:
        if cls._pool is None:
            load_dotenv()
            
            cls._pool = pooling.MySQLConnectionPool(
                pool_name="connectionPool",
                pool_size=5,
                host="localhost",
                user=getenv("DATABASE_USERNAME"),
                password=getenv("DATABASE_PASSWORD"),
                database=getenv("DATABASE")
            )
            
        return cls._pool.get_connection()