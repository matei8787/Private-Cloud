import logging

from core.security import bruteforce, user_agent
from core.utils.client_ip import get_client_ip

logger = logging.getLogger("ovpn.security")


class IDSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, req):
        ip = get_client_ip(req)
        ua = req.META.get("HTTP_USER_AGENT", "unknown")
        path = req.get_full_path()

        if bruteforce.get_failed_attempts(ip) > bruteforce.MAX_WARN:
            logger.warning("IP %s tried too many times in a row", ip)

        if user_agent.is_forbidden(ua):
            logger.warning(
                "Forbidden user-agent detected IP=%s, UA=%s, Path=%s", ip, ua, path
            )

        return self.get_response(req)
