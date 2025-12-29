from django.http import HttpResponse
from core.security import bruteforce, user_agent

class IPSMiddleware:
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

        
        if user_agent.is_forbidden(ua):
            return HttpResponse("Forbidden!", status=403)
        
        if bruteforce.is_banned(ip):
            return HttpResponse("Forbidden!", status=403)
        
        req.client_ip = ip
        
        return self.get_response(req)