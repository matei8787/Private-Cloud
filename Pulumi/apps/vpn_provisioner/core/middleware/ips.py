from django.http import HttpResponse

from core.security import bruteforce, user_agent
from core.utils.client_ip import get_client_ip


class IPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, req):
        ip = get_client_ip(req)
        ua = req.META.get("HTTP_USER_AGENT", "unknown")

        # Set before any early return so ReqLoggerMiddleware always has it.
        req.client_ip = ip

        if user_agent.is_forbidden(ua):
            return HttpResponse("Forbidden!", status=403)

        if bruteforce.is_banned(ip):
            return HttpResponse("Forbidden!", status=403)

        return self.get_response(req)
