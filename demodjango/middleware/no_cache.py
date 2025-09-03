from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class NoCacheForHtmlMiddleware(MiddlewareMixin):
    """
    Prevent browsers from serving cached HTML after logout/back button.
    Skips static and media URLs so assets can keep their normal caching.
    """
    def process_response(self, request, response):
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type.lower():
            return response

        static_url = getattr(settings, 'STATIC_URL', '') or ''
        media_url = getattr(settings, 'MEDIA_URL', '') or ''
        path = request.path or ''

        if (static_url and path.startswith(static_url)) or (media_url and path.startswith(media_url)):
            return response

        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
