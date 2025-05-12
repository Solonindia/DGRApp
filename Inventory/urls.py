from django.urls import path
from . import views
from demoapp.views import admin_login_view,user_login_view

urlpatterns = [
    path('upload/', views.upload_inventory, name='upload_inventory'),
    path('edit/<str:site_name>/', views.edit_inventory, name='edit_inventory'),
    path('inventory_history/<str:site_name>/', views.inventory_history, name='inventory_history'),
    path('notification_list/',views.notification_list, name='notification_list'),
    path('real-time-notifications/', views.real_time_notification_list, name='real_time_notification_list'),
    path('site-analysis/', views.site_analysis, name='site_analysis'),
    path('edit-inventory/<int:inventory_id>/', views.edit_inventory1, name='edit_inventory1'),
    path('inventory/stock-report/<str:site_name>/', views.stock_report_view, name='stock_report'),
    path('inventory/export-stock-report/<str:site_name>/', views.export_stock_report_excel, name='export_stock_report'),

]
