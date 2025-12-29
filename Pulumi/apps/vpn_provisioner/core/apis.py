import requests
from django.conf import settings
import logging

logger = logging.getLogger('django')

def safe_delete(url, headers, payload={}, timeout=10):
    try:
        res = requests.delete(url, json=payload, headers=headers, verify=settings.VERIFY_SSL, timeout=timeout)
        data = res.json()
        res.raise_for_status()  # raises for HTTP 4xx/5xx
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {e}"}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": True, "data": data.get("data")}

def safe_post(url, headers, payload, timeout=10):
    try:
        res = requests.post(url, json=payload, headers=headers, verify=settings.VERIFY_SSL, timeout=timeout)
        data = res.json()
        res.raise_for_status()  # raises for HTTP 4xx/5xx
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {e}"}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": True, "data": data.get("data")}


def safe_get(url, headers, payload={}, timeout=10):
    try:
        res = requests.get(url, params=payload, headers=headers, verify=settings.VERIFY_SSL, timeout=timeout)
        data = res.json()
        res.raise_for_status()  # raises for HTTP 4xx/5xx
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {e}"}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": True, "data": data.get("data")}

def safe_patch(url, headers, payload={}, timeout=10):
    try:
        res = requests.patch(url, json=payload, headers=headers, verify=settings.VERIFY_SSL, timeout=timeout)
        res.raise_for_status()  # raises for HTTP 4xx/5xx
        data = res.json()
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {e}"}
    except ValueError:
        return {"success": False, "error": "Invalid JSON response"}

    if data.get("status") != "ok":
        return {"success": False, "error": data.get("message", "Unknown error")}
    
    return {"success": True, "data": data.get("data")}

class PfSenseAPI:
    def __init__(self):
        self.base = f"{settings.PFSENSE_HOST.rstrip('/')}/api/v2"
        self.key = settings.PFSENSE_KEY
        self.headers = {
            "X-API-KEY": self.key,
            "Content-Type": "application/json"
        }
        
    def generate_certificate(self, username, caref):
        url = f"{self.base}/system/certificate/generate"
        payload = {
            "descr": f"Certificate for {username}",
            "caref": str(caref),
            "keytype": "RSA",
            "keylen": 2048,
            "digest_alg": "sha256",
            "dn_commonname": f"{username}",
        }
        res = safe_post(url, self.headers, payload) 
        return res
    
    def upload_cert(self, username, crt, prv):
        url = f"{self.base}/system/certificate"
        
        payload = {
            "descr": f"Cert for {username}",
            "type": "user",
            "crt": crt,
            "prv": prv,
        }
        res = safe_post(url, self.headers, payload)
        return res
    
    def create_user(self, pfs_cert_refid, username, password=None):
        url = f"{self.base}/user"
        paswd = "default123" if password == None else password
        
        payload = {
            "name": username,
            "password": paswd,
            "descr": "Automated VPN user",
            "priv": [],
            "disabled": False,
            "cert": [str(pfs_cert_refid)]
        }
        res = safe_post(url, self.headers, payload)
        return res
    
    def generate_client_config(self, server, certref, username, passwd):
        url = f"{self.base}/vpn/openvpn/client_export/config"
        
        payload = {
                "server": server,
                "certref": str(certref),
                "username": username,
                "usepass": True,
                "pass": str(passwd),
            }
        return safe_post(url, self.headers, payload)
    
    def export_client(self, server, cert_id, username, cli_config_id, passwd):
        url = f"{self.base}/vpn/openvpn/client_export"
        
        payload = {
            "type": "confinline",
            "id": cli_config_id,
            "certref": cert_id,
            "username": username,
            "server": server,
            "usepass": True,
            "pass": str(passwd),
            "useaddr": "other",
            "useaddr_hostname": "dorbjojomatei.mooo.com",
        }
        try:
            
            res = requests.post(url, headers={**self.headers, "Accept": "*/*"}, json=payload, verify=settings.VERIFY_SSL, timeout=20)
            res.raise_for_status()
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
        return {"success": True, "file": res.content}

    def attach_cert_user(self, username, ref_id):
        url = f'{self.base}/users'
        res = safe_get(url, self.headers)
        users = res['data']
        uid = -1
        for user in users:
            if user['name'] == username:
                uid = user['id']
                break
        if uid is None:
            return {"success": False, "error": "User not found"}
        url = f'{self.base}/user'
        payload = {
            'id': uid,
            'cert': [ref_id],
        }
        res = safe_patch(url, self.headers, payload)
        return res
    
    def delete_cert(self, ref_id):
        url=f"{self.base}/system/certificates"
        res = safe_get(url, self.headers)
        certid = -1
        for cert in res['data']:
            if cert['refid'] == ref_id:
                certid = cert['id']
                break
        if certid == -1:
            return {"success": False, "error": "Certificate not found"}
        url = f"{self.base}/system/certificate"
        payload = {
            "id": certid,
        }
        res = safe_delete(url, self.headers, payload)
        if not res['success']:
            logger.info(f"Could not delete cert {certid} with ref {ref_id} with {res['error']}")
        return res
    
    def delete_user(self, username):
        url = f'{self.base}/users'
        res = safe_get(url, self.headers)
        users = res['data']
        uid = -1
        for user in users:
            if user['name'] == username:
                uid = user['id']
                break
        if uid is None:
            return {"success": False, "error": "User not found"}
        url = f'{self.base}/user'
        payload = {
            'id': uid,
        }
        res = safe_delete(url, self.headers, payload)
        if not res['success']:
            logger.info(f"Could not delete {username} with id {uid} with errors {res['error']}")
        return res
    
    def delete_client_config(self, certid):
        url = f"{self.base}/vpn/openvpn/client_export/config"
        payload = {
            'id': certid,
        }
        res = safe_delete(url, self.headers, payload)
        if not res['success']:
            logger.info(f"Could not delete client config for cert {certid} with {res['error']}")
        return res