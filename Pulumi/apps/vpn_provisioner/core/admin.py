from django.contrib import admin
from .models import LAN, Code, VPNCert, VPNClientConfig

# Register your models here.
admin.site.register(LAN)
admin.site.register(Code)
admin.site.register(VPNCert)
admin.site.register(VPNClientConfig)