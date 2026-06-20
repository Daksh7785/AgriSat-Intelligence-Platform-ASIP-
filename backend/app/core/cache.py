import redis.asyncio as redis
from loguru import logger
from typing import Optional

from app.core.config import settings

# Global redis client reference
redis_client: Optional[redis.Redis] = None

async def init_cache():
    """Establishes connection to Redis server."""
    global redis_client
    logger.info("Initializing Redis Cache connection...")
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established successfully.")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        # Allow running without redis if in local fallback mode
        redis_client = None

async def close_cache():
    """Gracefully closes Redis connection."""
    global redis_client
    if redis_client:
        logger.info("Closing Redis connection...")
        await redis_client.close()

async def cache_get(key: str) -> Optional[str]:
    """Retrieves cached value by key."""
    if not redis_client:
        return None
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warn(f"Redis get failed: {e}")
        return None

async def cache_set(key: str, value: str, expire_seconds: int = 3600):
    """Caches value with a defined expiration window."""
    if not redis_client:
        return
    try:
        await redis_client.set(key, value, ex=expire_seconds)
    except Exception as e:
        logger.warn(f"Redis set failed: {e}")
