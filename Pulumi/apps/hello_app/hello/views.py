from django.shortcuts import render
from .models import Aplicatie
# Create your views here.
def index(req):
    if req.method != 'GET':
        pass #TODO: Return a bad code or something
    
    return render(req, "hello/index.html", {
        "apps": Aplicatie.objects.all(),
    })