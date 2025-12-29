from django.utils import timezone
from datetime import timedelta, datetime
from ..models import VPNCert, Code, VPNClientConfig
from ..apis import PfSenseAPI
import logging
import os 

logger = logging.getLogger("django")
api = PfSenseAPI()

def renew_cert(cert):
    res = api.generate_certificate(cert.username, cert.pfpfs_cert_refid)
    if not res['success']:
        logger.info("Could not generate certificate to renew for user: %s\n%s", str(cert.username), str(res['errror']))
    
    crt = res['crt']
    prv = res['prv']
    
    res = api.upload_cert(cert.username, crt, prv)
    if not res['success']:
        logger.info("Could not upload new certificate to user %s\n%s", str(cert.username), str(res['error']))
    new_refid = res['data']['id']
        
    res = api.attach_cert_user(cert.username, new_refid)
    if not res['success']:
        logger.info("Could not attach new certificate %s to user %s\n%s", str(new_refid), str(cert.username), str(res['error']))
    # TODO: Update the DB and other things of necessary
    delete_cert(cert)
    res = api.delete_cert(cert.pfs_cert_refid)
    if not res['success']:
        logger.info("Could not delete certificate with id: %s", cert.pfs_cert_refid)
        return None

def check_exp_certs():
    soon = datetime.now(timezone.utc) + timedelta(days=3)
    exp_certs = VPNCert.objects.filter(expires_at__lte=soon, renewed=False, need_renew=True)
    for c in exp_certs:
        renew_cert(c)

def delete_code(code):
    Code.objects.filter(code=code.code).delete()

def delete_cert(vpncert):
    res = api.delete_cert(vpncert.pfs_cert_refid)
    if not res['success']:
        logger.info("Could not delete cert %s, %s", str(vpncert.pfs_cert_refid), str(res['error']))
    VPNCert.objects.filter(username=vpncert.username, lan=vpncert.lan).delete()
    aux = VPNClientConfig.objects.filter(certref=vpncert.pfs_cert_refid)
    configurari = list(aux)
    aux.delete()
    for c in configurari:
        res = api.delete_config(c.conf_id)
        if not res['success']:
            logger.info("Could not delete VPN config %s for cert %s, %s", str(c.conf_id), str(vpncert.pfs_cert_refid), str(res['error']))

def delete_config(vpnconfig):
    res = api.delete_client_config(vpnconfig.conf_id)
    if not res['success']:
        logger.info("Could not delete config %s, %s", str(vpnconfig.conf_id), str(res['error']))
    VPNClientConfig.objects.filter(username=vpnconfig.username, lan=vpnconfig.lan).delete()

def delete_codes():
    # TODO: Delete all need_deleted codes
    pass

def check_needs():
    codes_uses = Code.objects.filter(max_uses__lte=0)
    codes_expired = Code.objects.filter(expires_at__lte=datetime.now(timezone.utc))
    codes_uses.update(needs_deleted=True)
    codes_expired.update(needs_deleted=True)

