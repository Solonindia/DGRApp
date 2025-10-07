from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
import os
from django.views.generic import TemplateView
from django.contrib.staticfiles.storage import staticfiles_storage

def _serve(path, ctype, extra_headers=None):
    with open(path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=ctype)
    if extra_headers:
        for k,v in extra_headers.items():
            resp[k] = v
    return resp

def service_worker(request):
    # Read the built static file and return from root with correct headers
    file = staticfiles_storage.open('service-worker.js', 'rb')
    data = file.read()
    file.close()
    resp = HttpResponse(data, content_type='application/javascript')
    # Allow root scope control even if file lives under /static/
    resp['Service-Worker-Allowed'] = '/'
    # Prevent aggressive CDN/browser caching while you iterate
    resp['Cache-Control'] = 'no-cache'
    return resp

def webmanifest(request):
    p = os.path.join(settings.BASE_DIR, 'static', 'pwa', 'manifest.json')
    return _serve(p, 'application/manifest+json')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('demoapp.urls')),
    path('gatepass/',include('gatepass.urls')),
    path('inventory/',include('Inventory.urls')),
    path('service-report/',include('report.urls')),
    path('service-worker.js', service_worker, name='service_worker'),
    path('offline', TemplateView.as_view(template_name='offline.html'), name='offline'),
    # optional: serve manifest at root if you prefer
    path('manifest.webmanifest',
         TemplateView.as_view(template_name='manifest.webmanifest',
                              content_type='application/manifest+json'),
         name='pwa_manifest'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


