from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse, FileResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Code, VPNCert, VPNClientConfig, LAN
from .forms import VPNForm
from .apis import PfSenseAPI
from django.db import transaction, IntegrityError
from django.db.models import F
from django.views.decorators.http import require_POST
import base64
from django.utils.text import slugify
import json
import logging
import random
from core.security import bruteforce
app_logger = logging.getLogger("django")
sec_logger = logging.getLogger("ovpn.security")

# Create your views here.
@require_POST
def vpn_export_view(req):
    form = VPNForm(req.POST)
    if not form.is_valid():
        sec_logger.warning(
            "Invalid Form: %s",
            str(form.errors),
        )
        return JsonResponse({"success": False, "error": "Wrong form"}, status=400)
    username = form.cleaned_data['username']
    req_code = form.cleaned_data['code']
    password = form.cleaned_data['password']
    
    #verify the code
    code = Code.objects.filter(code=req_code).first()
    if not code or code.expires_at < timezone.now():
        sec_logger.warning("User %s used an incorrect code: %s", username, req_code)
        bruteforce.increment_failed_atempt(req.client_ip)
        return JsonResponse({"success": False, "error":"Invalid Code"}, status=400)

    bruteforce.reset_failed_attempts(req.client_ip)
    lan = code.lan
    # Validate LAN:
    if not LAN.objects.filter(id=lan.id).exists():
        sec_logger.warning("User %s tried to use a code for LAN %s", username, str(lan))
        return JsonResponse({"success": False, "error": "Internal server error"}, status=500)
    
    api = PfSenseAPI()
    #check if the user exists
    usercert = VPNCert.objects.filter(
        username=username,
        lan=lan,
    ).first()
    if not usercert:
        try:
            res = api.generate_certificate(username, code.caref)
            app_logger.info("Generating user Certificate for user: %s", str(username))
            if not res['success']:
                raise Exception(f"Certificate Generation Failed {res['error']}")
            data = res['data']
            refid = data.get('refid')
            crt = data.get('crt')
            expires_at = timezone.now() + timedelta(days=int(data.get('lifetime')))
            if not VPNCert.objects.filter(username=username).exists():
                res = api.create_user(refid, username, password)
                app_logger.info("Creating user %s with certificate code %s", str(username), str(refid))
                if not res['success']:
                    aux = api.delete_cert(refid)
                    if not aux['success']:
                        sec_logger.warning("Didn't finishdeleting certificate created %s", str(aux['error']))
                    raise Exception(f"User creation Failed {res['error']}")
            else:
                res = api.attach_cert_user(username, refid)
                app_logger.info("Attaching certificate %s to user %s", str(refid), str(username))
                if not res['success']:
                    api.delete_cert(refid)
                    raise Exception(f"Cert attachment failed: {res['error']}")
        except Exception as e:
            sec_logger.warning("Didn't finish usercert creation %s", str(e))
            api.delete_user(username)
            api.delete_cert(refid)
            return JsonResponse({"success": False, "error": "Internal Server Error"}, status=500)
        
        
        with transaction.atomic():
            try:
                # save to DB
                usercert = VPNCert.objects.create(
                username = username,
                lan = lan,
                cert = crt,
                pfs_cert_refid = refid,
                expires_at = expires_at,
                )
                app_logger.info(
                    "Saved VPN Cert for user %s in LAN %s",
                    username,
                    LAN.objects.get(id=lan.id).name,
                                )
                code = Code.objects.select_for_update().get(code=code.code)
                if code.max_uses <= 0:
                    sec_logger.warning("User %s used an invalid code %s", username, code.code)
                    api.delete_user(username)
                    api.delete_cert(usercert.pfs_cert_refid)
                    return JsonResponse({"success": False, "error": "Forbidden code"}, status=403)
                
                updated = Code.objects.select_for_update().filter(code=code.code).update(max_uses=F('max_uses')-1)
                if not updated:
                    app_logger.info("Code update failed for code: %s", code.code)
                    api.delete_user(username)
                    api.delete_cert(usercert.pfs_cert_refid)
                    return JsonResponse({"success": False, "error": "Internal Server error"}, status=500)
                
            except IntegrityError:
                sec_logger.warning("Too many code uses attempts, pottential brute force")
                api.delete_user(username)
                api.delete_cert(usercert.pfs_cert_refid)
                return JsonResponse({"success": False, "error": "Please, retry"}, status=409)
            except Exception as e:
                sec_logger.warning("Encontered internal problem DB transaction: %s", str(e))
                api.delete_user(username)
                api.delete_cert(usercert.pfs_cert_refid)
                return JsonResponse({"success": False, "error": "Internal Server error"}, status=500)
    
    config = VPNClientConfig.objects.filter(username=username, lan=lan).first()
    if not config:
        try:
            res = api.generate_client_config(lan.id, usercert.pfs_cert_refid, username, password)
            with transaction.atomic():
                config = VPNClientConfig.objects.create(
                    conf_id=res['data']['id'],
                    username=username,
                    lan=lan,
                    certref=usercert.pfs_cert_refid,
                )
        except Exception as e:
            sec_logger.warning("Config generation ERROR: %s", str(e))
            return JsonResponse({"success": False, "error":"Internal Server Error"}, status=500)
    
    try:
        res = api.export_client(lan.id, usercert.pfs_cert_refid, username, config.conf_id, password)
    except Exception as e:
        sec_logger.warning("Couldn't export client: %s", str(e))
        return JsonResponse({"success": False, "error":"Internal Server Error"}, status=500)
    if not res['success']:
        sec_logger.warning("Couldn't get the export config: %s", str(res['error']))
        return JsonResponse({"success": False, "error":"Internal Server Error"}, status=500)
        
    jdata = json.loads(res['file'].decode())
    binary = jdata['data']['binary_data']
    
    lines = binary.splitlines()
    clean_lines = []
    for l in lines:
        l = l.strip()
        if not l.startswith('pfSense-'):
            clean_lines.append(l)
    config_text = '\n'.join(clean_lines)
    safe_name = slugify(username) + slugify(lan.name) or "vpn"
    from io import BytesIO
    buf = BytesIO(config_text.encode())
    resp = FileResponse(buf, as_attachment=True, filename=f"{safe_name}.ovpn", content_type="application/x-openvpn-profile")
    app_logger.info(
        "User: %s downloaded config file using code %s",
        username,
        code.code,
    )
    return resp
    
def index_view(req):
    return render(req, "core/index.html", context={
        "form": VPNForm()
    })
    
def deceptive_view(req):
    fake_html = render_to_string("core/404.html")
    padding = " " * random.randint(0,5000)
    return HttpResponse(fake_html + padding, status=200)

def robots_view(req):
    return HttpResponse("""
                        User-agent: *\n
                        Disallow: *\n
                        """, status=200)