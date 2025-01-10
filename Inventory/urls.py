from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_inventory, name='upload_inventory'),
    path('edit/<str:site_name>/', views.edit_inventory, name='edit_inventory'),
    path('inventory_history/<str:site_name>/', views.inventory_history, name='inventory_history'),
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('notification_list/',views.notification_list, name='notification_list'),
    path('real-time-notifications/', views.real_time_notification_list, name='real_time_notification_list'),
    path('site-analysis/', views.site_analysis, name='site_analysis'),

]
