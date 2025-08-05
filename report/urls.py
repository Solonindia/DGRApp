from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_button_view, name='button_page'),
    path('form/', views.checklist_form_view, name='checklist_form'),
    path('add-checklist-item/', views.add_checklist_item_view, name='add_checklist_item'),
    path('checklist/preview/<int:response_id>/', views.checklist_preview_view, name='checklist_preview'),
    path('download-pdf/<int:response_id>/', views.download_pdf_view, name='download_pdf'),
    path('history/', views.history_page, name='history_servicereport'),

]
