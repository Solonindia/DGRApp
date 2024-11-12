# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.visitor_log_view, name='visitor_log'),  # Home page with the visitor log form
    path('visitor-log/', views.visitor_log_list, name='visitor_log_list'),  # List of visitor logs
    path('visitor-log-list/', views.visitor_log_list_user, name='visitor_log_list_user'), 
    path('gatepass/download/<int:gatepass_id>/', views.download_visitor_log_pdf, name='download_visitor_log_pdf'),
    path('visitor-log/<int:log_id>/delete/', views.delete_visitor_log, name='delete_visitor_log'),  # New URL for delete
    path('visitor-log-user/', views.visitor_log_user_view, name='visitor_log_user_view'),  # List of visitor logs
]