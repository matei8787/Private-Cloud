import logging

from django.contrib.auth.signals import user_login_failed

from core.security import bruteforce
from core.utils.client_ip import get_client_ip

security_logger = logging.getLogger("ovpn.security")


def handle_failure(sender, credentials, request, **kwargs):
    # This used to key on the raw X-Forwarded-For header, so the counter was
    # stored under "1.2.3.4, 10.0.0.1" while is_banned() looked up "1.2.3.4".
    # The keys never matched and no failed login ever produced a ban.
    if request is None:
        security_logger.warning("Login failure with no request object; cannot attribute it to an IP")
        return

    ip = get_client_ip(request)

    # increment_failed_attempt() owns the ban threshold and duration, so the
    # counting and the banning stay in one place.
    failed = bruteforce.increment_failed_attempt(ip)

    if failed > bruteforce.MAX_WARN:
        security_logger.warning("Failed login attempts from %s: %d", ip, failed)


user_login_failed.connect(handle_failure)
