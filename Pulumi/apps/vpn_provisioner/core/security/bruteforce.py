"""
Failed-attempt counting and IP bans, backed by Redis.

Callers must pass an IP obtained from core.utils.client_ip.get_client_ip, never a
raw header value. Keying on anything the client controls makes the counters
meaningless.

Fail-open on a Redis outage is deliberate: the alternative is that losing Redis
locks every user out of the VPN portal, which is the tool used to reach the
network in the first place. The outage is logged by get_redis(), and the trade is
a gap in brute-force protection rather than a self-inflicted denial of service.
"""

import logging

from core.utils.redis_test import get_redis

sec_logger = logging.getLogger("ovpn.security")

redis_cli = get_redis()

# Attempts before the security log starts warning.
MAX_WARN = 5
# Attempts before the IP is banned.
MAX_BAN = 10
BAN_HOURS = 48
# Sliding window for the attempt counter; refreshed on every failure.
WINDOW_SECONDS = 3600


def get_failed_attempts(ip):
    if not redis_cli:
        return 0
    value = redis_cli.get(f"failed:{ip}")
    return int(value) if value is not None else 0


def increment_failed_attempt(ip):
    if not redis_cli:
        return 0

    key = f"failed:{ip}"
    count = redis_cli.incr(key)
    redis_cli.expire(key, WINDOW_SECONDS)

    if count > MAX_BAN:
        redis_cli.setex(f"banned:{ip}", BAN_HOURS * 3600, 1)
        sec_logger.warning("%s banned for %d hours after %d failed attempts", ip, BAN_HOURS, count)

    return count


def reset_failed_attempts(ip):
    if not redis_cli:
        return None
    redis_cli.delete(f"failed:{ip}")


def is_banned(ip):
    if not redis_cli:
        return False
    return bool(redis_cli.exists(f"banned:{ip}"))
