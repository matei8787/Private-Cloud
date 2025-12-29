import logging
from django.contrib.auth.signals import user_login_failed
from core.utils.redis_test import get_redis
from core.security import bruteforce

security_logger = logging.getLogger("ovpn.security")

redis_cli = get_redis()

MAX_WARN = 5
MAX_BAN = 10
BAN_DURATION = 48


def handle_failure(sender, credentials, request, **kwargs):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown"))
    failed = bruteforce.increment_failed_atempt(ip)
    
    if failed > MAX_WARN:
        security_logger.warning(
            f"Too many failed admin login attempts from {ip}: {failed}"
        )

    if failed > MAX_BAN:
        redis_cli.setex(f"banned:{ip}", BAN_DURATION*3600, 1)
        security_logger.warning(
            f"IP {ip} banned for {BAN_DURATION//24} days"
        )


user_login_failed.connect(handle_failure)