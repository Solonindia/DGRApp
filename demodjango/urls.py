from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, FileResponse
from django.views.generic import TemplateView
from django.contrib.staticfiles.storage import staticfiles_storage
import os

def favicon(request):
    icon_path = os.path.join(settings.BASE_DIR, 'static', 'favicon.ico')
    if os.path.exists(icon_path):
        return FileResponse(open(icon_path, 'rb'), content_type='image/x-icon')
    return HttpResponse("favicon not found", status=404)

# -----------------------------------------------------------
# Utility helper: Serve static-like files with correct headers
# -----------------------------------------------------------
def _serve(path, ctype, extra_headers=None):
    """Serve a file from disk with proper Content-Type."""
    with open(path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=ctype)
    if extra_headers:
        for k, v in extra_headers.items():
            resp[k] = v
    return resp

# -----------------------------------------------------------
# ✅ Service Worker route (must be at root scope)
# -----------------------------------------------------------
def service_worker(request):
    """
    Serve the PWA service-worker.js file from the static directory.
    Chrome requires it at the root ('/service-worker.js') to control all pages.
    """
    try:
        with staticfiles_storage.open('service-worker.js') as f:
            data = f.read()
        resp = HttpResponse(data, content_type='application/javascript')
        resp['Service-Worker-Allowed'] = '/'   # Full scope control
        resp['Cache-Control'] = 'no-cache'     # Avoid stale versions
        return resp
    except Exception as e:
        return HttpResponse(str(e), status=500)

# -----------------------------------------------------------
# ✅ Web App Manifest route (for PWA install support)
# -----------------------------------------------------------
def webmanifest(request):
    p = os.path.join(settings.BASE_DIR, 'static', 'manifest.webmanifest')
    return _serve(p, 'application/manifest+json')

# -----------------------------------------------------------
# ✅ URL Patterns
# -----------------------------------------------------------
urlpatterns = [
    path('admin/', admin.site.urls),

    # Include app routes
    path('', include('demoapp.urls')),
    path('gatepass/', include('gatepass.urls')),
    path('inventory/', include('Inventory.urls')),
    path('service-report/', include('report.urls')),
    path('favicon.ico', favicon, name='favicon'),
    # PWA specific routes
    path('service-worker.js', service_worker, name='service_worker'),
    path('manifest.webmanifest', webmanifest, name='manifest'),
    # Offline fallback page (for PWA offline support)
    path('offline', TemplateView.as_view(template_name='offline.html'), name='offline'),
]

# -----------------------------------------------------------
# ✅ Static & Media file serving (only in DEBUG mode)
# -----------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
