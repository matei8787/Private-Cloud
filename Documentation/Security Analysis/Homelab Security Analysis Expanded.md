## 1. Executive Summary

This document outlines the security posture of the homelab infrastructure and the custom VPN Provisioner application. The security strategy follows a **Defense in Depth** approach, layering controls across the physical, network, and application layers. By integrating enterprise-grade principles—such as Least Privilege, Network Segmentation, and Attack Surface Reduction—the system is designed to withstand common vectors including Man-in-the-Middle (MITM) attacks, pivoting, and automated reconnaissance.

## 2. Network Security & Infrastructure Hardening

### 2.1 Public Key Infrastructure (PKI) Hierarchy

**Threat Vector:** Man-in-the-Middle (MITM) attacks and unauthorized service spoofing. **Control:** Hierarchical Internal PKI.

To ensure encrypted and authenticated communication between internal services and users, a strict Public Key Infrastructure (PKI) was deployed. Rather than using a flat trust model, the architecture utilizes a tiered approach:

- **Root CA:** Kept isolated; its sole purpose is to sign Intermediate CAs.
- **Intermediate CAs:**
    - _Services CA:_ Issues certificates for the internal service trust domain (Traefik reverse proxy, Nginx).
    - _Users CA:_ Issues client certificates for user authentication.
    - _Management CA:_ Dedicated to infrastructure management services (VPN). This segmentation ensures that a compromise of a specific intermediate CA (e.g., the web services layer) does not compromise the integrity of the root or other unrelated domains.
### 2.2 Network Segmentation (DMZ & VLANs)

**Threat Vector:** Lateral Movement (Pivoting). **Control:** Virtual LANs (VLANs) and Bridge Isolation via Proxmox/pfSense.

The network topology adheres to the Principle of Least Privilege regarding network visibility. The infrastructure is divided into distinct zones:

- **DMZ (Demilitarized Zone):** Contains the Traefik reverse proxy. It has strictly limited connectivity to the internal network.
    
- **Services Network:** Hosts the backend logic and databases.
    
- **Management/Admin Network:** Restricted to administrative traffic. Traffic between these zones must pass through the pfSense core router, prohibiting direct Layer 2 communication. This prevents an attacker who compromises a web-facing service in the DMZ from unrestricted pivoting to critical databases in the Services network.
    

### 2.3 Firewall Strategy

**Threat Vector:** Unauthorized port access and service exploitation. **Control:** Hybrid Firewall approach (Network + Host-based).

- **Network Layer (pfSense):** A stateful firewall policy is enforced at the network edge and between VLANs. Rules are granular, allowing traffic only on specific ports required for business logic (e.g., Traefik to App on port 443/80, but blocking SSH/22).
    
- **Host Layer (UFW):** To implement Zero Trust inside the network perimeter, `ufw` (Uncomplicated Firewall) is configured on every Virtual Machine. Even if the network firewall is bypassed, individual servers reject connections on non-essential ports, effectively stopping lateral enumeration.
    

### 2.4 Attack Surface Reduction

**Threat Vector:** Public Service Exploitation and Zero-Day Vulnerabilities. **Control:** VPN-Only Access Model.

To minimize the external attack surface, no internal services (databases, dashboards, management interfaces) are exposed directly to the public internet. All access to the private cloud environment is tunneled through an OpenVPN gateway hosted on pfSense. This ensures that an attacker must first breach the VPN encryption and authentication layer before they can even attempt to interact with the internal applications.

## 3. Application Security (AppSec)

### 3.1 Intrusion Detection & Prevention (IDS/IPS)

**Threat Vector:** Brute-force attacks and credential stuffing. **Control:** Custom Middleware IDS/IPS.

The VPN Provisioner application implements a custom middleware solution to detect and mitigate authentication attacks:

- **IDS (Detection):** Monitors login attempts and triggers alerts upon crossing a low threshold of failures.
    
- **IPS (Prevention):** Automatically bans the source IP address after a secondary, higher threshold of failed attempts is reached. This effectively neutralizes automated brute-force scripts by denying them the request volume needed to succeed.
    

### 3.2 Anti-Reconnaissance Mechanisms

**Threat Vector:** Vulnerability Scanners and Bot Enumeration. **Control:** Deceptive Responses and User-Agent Blacklisting.

To confuse automated scanners (e.g., Nikto, Gobuster), the application employs active deception:

- **Deceptive View:** Scanners often filter out 404 (Not Found) responses to identify valid paths. The application intercepts specific invalid requests and returns a generic `HTTP 200 OK` status accompanied by randomized HTML padding. This "poisons" the scanner's data, flooding it with false positives.
    
- **Blacklisting:** The system identifies and blocks IP addresses presenting User-Agents associated with known attack tools (e.g., `sqlmap`, `nmap`).
    

### 3.3 OWASP Top 10 Mitigation

The application architecture addresses critical web vulnerabilities through secure coding practices:

- **Broken Access Control:** Access logic is encapsulated within private, non-public code. All failed access attempts are logged for audit trails.
    
- **Injection (SQLi):** Direct database interaction is avoided. All data persistence is delegated to the ORM layers of Postgres and Redis, and input forms are rigorously sanitized before processing.
    
- **Cross-Site Request Forgery (CSRF):** Django’s built-in `csrf_token` middleware is enforced on all state-changing requests, ensuring that actions cannot be executed on behalf of authenticated users without their knowledge.
    
- **Cross-Site Scripting (XSS):** The application adheres to a strict separation of data and presentation. User input is processed exclusively in the backend and is never rendered raw in the DOM, neutralizing stored and reflected XSS vectors.
    

## 4. System Hardening

### 4.1 Privilege Escalation Defense

**Threat Vector:** Root compromise via weak credentials. **Control:** Root Login Disabled.

Following standard server hardening procedures, direct root login via SSH is disabled across all nodes. Administrative tasks must be performed via `sudo` with user-specific audit trails, preventing a single compromised root password from granting total system control.