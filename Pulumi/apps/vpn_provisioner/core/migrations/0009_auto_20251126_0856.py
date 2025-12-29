from django.db import migrations
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password


def create_defaults(apps, schema_editor):
    LAN = apps.get_model("core", "LAN")

    _, _ = LAN.objects.get_or_create(
        id=1,
        defaults={
            "name": "Server Network",
            "subnet_vpn": "10.0.1.0/24",
            "subnet_lan": "192.168.1.0/24",
        },
    )
    _, _ = LAN.objects.get_or_create(
        id=2,
        defaults={
            "name": "Client Network",
            "subnet_vpn": "10.0.2.0/24",
            "subnet_lan": "192.168.2.0/24",
        },
    )
    _, _ = LAN.objects.get_or_create(
        id=1,
        defaults={
            "name": "DMZ Network",
            "subnet_vpn": "10.0.3.0/24",
            "subnet_lan": "192.168.3.0/24",
        },
    )
    _, _ = LAN.objects.get_or_create(
        id=1,
        defaults={
            "name": "Admin Network",
            "subnet_vpn": "10.0.42.0/24",
            "subnet_lan": "all",
        },
    )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_code_needs_deleted'),
    ]

    operations = [
        migrations.RunPython(create_defaults),
    ]
