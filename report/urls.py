from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_button_view, name='button_page'),
    path('form/', views.checklist_form_view, name='checklist_form'),
    path('add-checklist-item/', views.add_checklist_item_view, name='add_checklist_item'),
    path('checklist/preview/<int:response_id>/', views.checklist_preview_view, name='checklist_preview'),
    path("checklist/pdf/<int:response_id>/", views.view_pdf_view, name="view_pdf"),
    path("checklist/pdf/<int:response_id>/download/", views.download_pdf_view, name="download_pdf"),
    path('history/', views.history_page, name='history_servicereport'),
    path("my-history/", views.history_page, name="my_history_servicereport"),


]
