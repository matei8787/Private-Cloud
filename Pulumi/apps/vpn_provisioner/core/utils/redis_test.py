import redis
import os
import logging

logger = logging.getLogger("django")

def get_redis():
    try:
        r=redis.Redis(
            host=os.environ.get("REDIS_HOST"),
            port=int(os.environ.get("REDIS_PORT")),
            db=0,
            decode_responses=True,
        )
        r.ping()
        return r
    except Exception as e:
        logger.info("Redis connection couldn't be established %s", str(e))
        return None