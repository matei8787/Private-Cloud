from core.utils.redis_test import get_redis
import logging

sec_logger = logging.getLogger("ovpn.security")
redis_cli = get_redis()

MAX_WARN = 5
MAX_BAN = 10
BAN_HOURS = 48

def get_failed_attempts(ip):
    if not redis_cli:
        return 0
    key=f"failed:{ip}"
    if not redis_cli.exists(key):
        return 0
    return int(redis_cli.get(key))

def increment_failed_atempt(ip):
    if not redis_cli:
        return 0
    key=f"failed:{ip}"
    count = redis_cli.incr(key)
    redis_cli.expire(key, 3600)
        
    if count > MAX_BAN:
        ban_key = f"banned:{ip}"
        redis_cli.setex(ban_key, BAN_HOURS * 3600, 1)
        sec_logger.warning("%s banned for 2 days", str(ip))
    
    return count

def reset_failed_attempts(ip):
    if not redis_cli:
        return None
    redis_cli.delete(f"failed:{ip}")
    
def is_banned(ip):
    if not redis_cli:
        return 0
    return redis_cli.exists(f"banned:{ip}")