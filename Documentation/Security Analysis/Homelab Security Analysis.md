# From pfSense
## Attack: Man-in-the-Middle (MITM)
## Defense: Public Key Infrastructure (PKI)

![CAs architecture](./Pasted%20image%2020260202130939.png)
#### Description:
- Root Certificate Authority (CA) only gives certificates to create internal, Intermediate CAs.
- Services CA gives certificates for internal services trust domain (Traefik-Nginx)
- Users CA gives certificates to users for the cloud
- Management CA gives certificates to other internal services (VPN servers)

## Attack: Pivoting
## Defense: Network Segmentation
![Network segmentation architecture](./Pasted%20image%2020260202131702.png)
#### Description:
- The DMZ network and the internal Services network are separated from each other and have to go through pfSense to talk to each other.
## Defense: Stateful Firewall
#### Description:
- Implemented granular firewall rules based on IPs and Ports inside pfSense Firewall (details if needed)
- This prevents someone from opening a communication channel on other ports than the ones that are already services listening.
## Attack: Public access => Big attack surface
## Defense: Reducing the attack surface by accessing the private cloud only via VPN.
![VPN Server attack surface reduction](./Pasted%20image%2020260202133639.png)
#### Description:
- Implemented VPN access for reducing the accessibility of the internal services.
- This reduces the attack surface of the system because there are no public facing internal services. 
# From other stuff
## Attack: Brute-forcing entry codes
## Defense: Middleware IDS/IPS
#### Description:
- Implemented a custom IDS/IPS for brute-forcing the VPN_Provisioner app.
- Creatied an IDS that alerts after a small threshold of unsuccessful login attempts
- Created an IPS that bans the IP after a bigger threshold of unsuccessful login attempts
## Attack: Pivoting
## Defense: UFW Firewall autoconfiguration
#### Description:
- Implemented strict ufw firewall rules on each machine based on it's needs. 
- This prevents someone from opening a communication channel on other ports than the ones that are already services listening.
## Attack: Privilege Escalation
## Defense: Disable root login
#### Description:
- Hardened the devices by disabling root login and not letting malicious actors Escalate privileges
## Attack: Reconnaissance (Recon)
## Defense: Deceiving view
#### Code:
``` python
def deceptive_view(req):
	fake_html = render_to_string("core/404.html")
	padding = " " * random.randint(0,5000)
	return HttpResponse(fake_html + padding, status=200)
```
#### Description:
- Recon tools can be configured to filter the responses from 404 pages or some length.
- Thus, if we add some padding and send status 200, the bots will show hits of different urls that go to the same dummy site.

## Defense: Blacklist known scanners
#### Description:
- Used known scanners (nmap, sqlmap, nikto, gobuster, etc) to ban IPs that have a user-agent that contains the names of one of these scanners.

# OWASP TOP 10
## Broken Access Control
#### Defense: The entry architecture is based on a code that is not public. 
#### Defense: We logged every unsuccessful login attempt

## Injection:
#### Defense: Sanitize the forms before processing it.
## Cross-site Request Forgery (CSRF)
#### Defense: We use csrf_token from django

# The best defense for any technology: DON'T USE IT
## Attack: SQL Injection
#### We delegate all the database operations to postgres and redis.
## Attack: Cross-site Scripting (XSS)
#### We never render user input on our site. We just use it in the backend.