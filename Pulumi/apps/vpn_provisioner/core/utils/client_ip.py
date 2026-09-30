"""
Single source of truth for the client IP.

Why this file exists: the IDS/IPS middleware used to read the left-most entry of
X-Forwarded-For. That entry is whatever the client sent, so anyone could rotate a
fake value per request and never accumulate failed attempts or hit a ban. Rate
limiting and IP bans built on a spoofable identifier are decoration.

The only entries in X-Forwarded-For that can be trusted are the ones our own
proxies appended, counted from the right. The request path is:

    client -> Traefik (DMZ) -> Nginx (services) -> Django

Traefik sets X-Forwarded-For to the peer it sees, discarding whatever the client
sent, because its forwardedHeaders.trustedIPs list is empty. Nginx then appends
Traefik's address. So the header arrives as:

    "<client>, <traefik>"

which means the client sits one position from the right: index -2. That is
XFF_TRUSTED_HOPS = 1, the number of trailing entries our own infrastructure adds
after the client. Change it if a proxy is added or removed, and keep it in sync
with Traefik's trustedIPs.

If the header is shorter than expected, the request did not come through the
expected chain, so REMOTE_ADDR is used instead and the mismatch is logged. That
fails closed: an attacker cannot shorten the chain to get a spoofed value
trusted, they can only fall back to their real address.
"""

import ipaddress
import logging
import os

logger = logging.getLogger("ovpn.security")

# Number of trailing X-Forwarded-For entries added by our own proxies.
XFF_TRUSTED_HOPS = int(os.environ.get("XFF_TRUSTED_HOPS", "1"))

UNKNOWN = "unknown"


def _valid(addr):
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False


def get_client_ip(request):
    """Return the client IP, or "unknown" if it cannot be established."""
    remote_addr = request.META.get("REMOTE_ADDR") or UNKNOWN
    raw = request.META.get("HTTP_X_FORWARDED_FOR")

    if not raw:
        # Direct hit on the app, bypassing the proxies. Nothing to unwrap.
        return remote_addr

    chain = [part.strip() for part in raw.split(",") if part.strip()]
    index = len(chain) - 1 - XFF_TRUSTED_HOPS

    if index < 0:
        logger.warning(
            "X-Forwarded-For shorter than the %d expected proxy hops (%r); "
            "falling back to REMOTE_ADDR %s",
            XFF_TRUSTED_HOPS,
            raw,
            remote_addr,
        )
        return remote_addr

    candidate = chain[index]
    if not _valid(candidate):
        logger.warning(
            "X-Forwarded-For entry %r is not an IP address (%r); "
            "falling back to REMOTE_ADDR %s",
            candidate,
            raw,
            remote_addr,
        )
        return remote_addr

    return candidate
