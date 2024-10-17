# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.visitor_log_view, name='visitor_log'),  # Home page with the visitor log form
    path('visitor-log/', views.visitor_log_list, name='visitor_log_list'),  # List of visitor logs
    path('download/<int:log_id>/', views.download_visitor_log_pdf, name='download_visitor_log_pdf'),  # Download PDF
    path('visitor-log/<int:log_id>/delete/', views.delete_visitor_log, name='delete_visitor_log'),  # New URL for delete
]