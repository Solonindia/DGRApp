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
    try:
        with staticfiles_storage.open('service-worker.js') as f:
            data = f.read()
        resp = HttpResponse(data, content_type='application/javascript')
        resp['Service-Worker-Allowed'] = '/'
        resp['Cache-Control'] = 'no-cache'
        return resp
    except Exception as e:
        return HttpResponse(str(e), status=500)

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


