from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import os

def _serve(path, ctype, extra_headers=None):
    with open(path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=ctype)
    if extra_headers:
        for k,v in extra_headers.items():
            resp[k] = v
    return resp

def service_worker(request):
    p = os.path.join(settings.BASE_DIR, 'DGRApp', 'static', 'pwa', 'service-worker.js')
    return _serve(p, 'application/javascript', {'Service-Worker-Allowed': '/', 'Cache-Control': 'no-cache'})

def webmanifest(request):
    p = os.path.join(settings.BASE_DIR, 'DGRApp', 'static', 'pwa', 'manifest.json')
    return _serve(p, 'application/manifest+json')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('demoapp.urls')),
    path('gatepass/',include('gatepass.urls')),
    path('inventory/',include('Inventory.urls')),
    path('service-report/',include('report.urls')),
    path('service-worker.js', service_worker),
    path('manifest.json', webmanifest),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


