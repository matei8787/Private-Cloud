from django.urls import path, re_path
from .views import index_view, vpn_export_view, deceptive_view, robots_view
from django.conf import settings

urlpatterns = [
    path('index/', index_view, name="index"),
    path('download/', vpn_export_view, name="export"),
    path('robots.txt', robots_view, name="robots"),
]