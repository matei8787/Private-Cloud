import logging
from core.security import bruteforce, user_agent

logger = logging.getLogger("ovpn.security")

class IDSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, req):
        ip = req.META.get("HTTP_X_FORWARDED_FOR", "unknown")
        if ip != "unknown":
            ip = [h.strip() for h in ip.split(",")]
            ip = ip[0]
        else:
            ip = req.META.get("REMOTE_ADDR", "unknown")
        ua = req.META.get("HTTP_USER_AGENT", "unknown")
        path = req.get_full_path()
        
        if bruteforce.get_failed_attempts(ip) > bruteforce.MAX_WARN:
            logger.warning("IP %s tried too many times in a row", str(ip))
        
        if user_agent.is_forbidden(ua):
            logger.warning("Forbidden user-agent detected IP=%s, UA=%s, Path=%s", str(ip), str(ua), str(path))

        return self.get_response(req)