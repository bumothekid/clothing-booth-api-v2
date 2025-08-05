from time import time, sleep
from flask import jsonify, make_response
from flask_limiter import Limiter, RequestLimit
from flask_limiter.util import get_remote_address
from .logging import Logger
from redis import Redis, RedisError

logger = Logger.getLogger()

def rateLimitResponse(rateLimit: RequestLimit):
    reset_in_seconds = rateLimit.reset_at - time()
    
    return make_response(jsonify({"error": f"Rate limit exceeded and will reset in {reset_in_seconds:.0f} seconds."}), 429)

def checkRedisConnection(limiter: Limiter):
    if not limiter.enabled:
        return
    
    retries = 0
    max_retries = 10
    retry_delay = 10

    while retries < max_retries:
        try:
            redis_client = Redis.from_url(limiter._storage_uri)
            redis_client.ping()
            redis_client.close()
            logger.info("Successfully connected to Redis.")
            return
        except RedisError as e:
            retries += 1
            logger.error(f"Failed to connect to Redis (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                sleep(retry_delay)
            else:
                logger.error("Max retries reached. Unable to connect to Redis.")
                raise e

try:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379",
        on_breach=rateLimitResponse
    )
    
    logger.debug(f"Rate limiter enabled: {limiter.enabled}")
    
    checkRedisConnection(limiter)
except RedisError as e:
    logger.error("Failed to connect to Redis")
    raise e
except Exception as e:
    logger.error("Failed to initialize rate limiter")
    logger.error(e)
    raise e