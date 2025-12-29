FORBIDDEN = ["sqlmap", "nikto", "nessus", "acunetix", "nmap", "gobuster", "dirbuster"]

def is_forbidden(user_agent):
    ua = (user_agent or "").lower()
    return any(f in ua for f in FORBIDDEN)