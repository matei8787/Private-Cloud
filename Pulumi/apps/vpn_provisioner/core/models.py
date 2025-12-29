from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
import base64

# Generate once: base64.urlsafe_b64encode(32-byte key)
FERNET_KEY = base64.urlsafe_b64encode(settings.SECRET_KEY.encode().ljust(32)[:32])

def encrypt_value(value: str) -> str:
    f = Fernet(FERNET_KEY)
    return f.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    f = Fernet(FERNET_KEY)
    return f.decrypt(token.encode()).decode()


# Create your models here.
class LAN(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=25)
    subnet_vpn = models.CharField(max_length=25)
    subnet_lan = models.CharField(max_length=25)
    
    def __str__(self):
        return f"{self.id}: {self.name}"

class Code(models.Model):
    code = models.CharField(primary_key=True, max_length=20)
    lan = models.ForeignKey(LAN, on_delete=models.CASCADE, related_name="codes")
    caref = models.CharField(max_length=100)
    expires_at = models.DateTimeField(null=False,blank=False)
    max_uses = models.IntegerField(default=1,null=False,blank=False)
    needs_deleted = models.BooleanField(default=False,null=False,blank=False)
    def __str__(self):
        return f"Code for LAN {self.lan.name}"
    
class VPNCert(models.Model):
    username = models.CharField(max_length=20)
    lan = models.ForeignKey(LAN, on_delete=models.CASCADE, related_name="certificates")
    
    cert = models.TextField()
    
    pfs_cert_refid = models.CharField(max_length=100, null=True, blank=True)
    
    expires_at = models.DateTimeField()
    need_renew = models.BooleanField(default=False)
    renewed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username','lan'], name='unique_user_per_lan')
        ]

    def __str__(self):
        return f"{self.username} Certificate"
    
    
class VPNClientConfig(models.Model):
    conf_id = models.IntegerField(unique=True)
    username = models.CharField(max_length=20)
    lan = models.ForeignKey(LAN, on_delete=models.CASCADE, related_name="configs")
    certref = models.CharField(max_length=25)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username','lan'], name='Unique_config_user_per_lan')
        ]