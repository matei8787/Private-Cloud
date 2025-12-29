from django.test import TestCase
from django.urls import reverse
from core.models import Code, LAN, VPNCert, VPNClientConfig
from django.utils import timezone
from datetime import timedelta
import json
from core.apis import PfSenseAPI
import logging
import os

logger = logging.getLogger("test")
TESTING_CA = os.environ.get("PFSENSE_TEST_CA")

class CodeAPITest(TestCase):
    def setUp(self):
        self.api = PfSenseAPI()
        self.lan = LAN.objects.get(id=1)
        self.code = Code.objects.create(
            code = "testcode",
            lan = self.lan,
            caref = TESTING_CA,
            expires_at = timezone.now() + timedelta(days=15),
            max_uses=1,
            needs_deleted=False,
        )
    
    def test_code_usage_limit(self):
        codes = Code.objects.all()
        print(codes.count())
        print(codes.first().code)
        res = self.client.post(reverse("export"), {
            "username": "testuser1",
            "password": "testpass1",
            "code": "testcode",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(VPNCert.objects.count(), 1)
        self.assertEqual(VPNClientConfig.objects.count(), 1)
        
        cert = VPNCert.objects.all().first()
        delres = self.api.delete_user("testuser1")
        self.assertTrue(delres['success'])
        certref = cert.pfs_cert_refid
        delres = self.api.delete_cert(certref)
        self.assertTrue(delres['success'])
        
        
        res2 = self.client.post(reverse("export"), {
            "username": "testuser2",
            "password": "testpass2",
            "code": "testcode",
        })
        self.assertNotEqual(res2.status_code, 200)
        data2 = json.loads(res2.content)
        self.assertFalse(data2['success'])
        
    def test_code_expired(self):
        self.code.expires_at = timezone.now() - timedelta(days=3)
        self.code.save()
        res = self.client.post(reverse("export"), {
            "username": "testuser1",
            "password": "testpass1",
            "code": "testcode",
        })
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.content)
        self.assertFalse(data['success'])