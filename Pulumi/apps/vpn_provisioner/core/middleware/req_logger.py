import logging
from time import time

logger = logging.getLogger("ovpn.requests")

class ReqLoggerMiddleware:
    def __init__(self, get_res):
        self.get_res = get_res
    
    def __call__(self, req):
        t0 = time()
        res = self.get_res(req)
        t1 = time()
        logger.info(
            "%s %s %s %s %d %.3f",
            req.client_ip,
            req.method,
            req.get_full_path(),
            req.META.get("HTTP_USER_AGENT", "-"),
            res.status_code,
            (t1 - t0),
        )
        return res