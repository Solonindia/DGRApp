# complaint/urls.py
from django.urls import path
from . import views
from gatepass.views import visitor_log_view,visitor_log_list,download_visitor_log_pdf,delete_visitor_log,visitor_log_user_view,visitor_log_list_user

urlpatterns = [
    path('', views.redirect_to_home),  
    path('home/', views.home_page, name='home'),
    path('superuser/signup/', views.signup_view, name='signup'),
    path('user/login/', views.login_view, name='login'),  
    path('superuser/login/',views.login1_view,name="login1"),
    path('superuser/services/', views.admin_page, name='admin'),
    path('user/services/', views.user_page, name='user'),
    path('user/newcomplaint/', views.complaint_form, name='complaint_form'),
    path('user/new/', views.complaint_form, name='new_complaint'),
    path('user/history/', views.final_complaints_user, name='final_complaints_user'),
    path('superuser/approval/', views.approval_complaints, name='approval_complaints'),
    path('superuser/approve_complaint/<int:complaint_id>/', views.accept_complaint, name='accept_complaint'),
    path('user/existing/', views.existing_complaints, name='existing_complaints'),
    path('user/edit/<int:complaint_id>/', views.edit_complaint, name='edit_complaint'),
    path('superuser/history/', views.final_complaints, name='final_complaints'),
    path('delete_complaint/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('complaint_analysis/', views.complaint_analysis, name='complaint_analysis'),
    path('complaints/<str:type>/<str:site_name>/', views.ComplaintDetailView, name='complaints_detail'),
    path('superuser/', visitor_log_view, name='visitor_log'),  # Home page with the visitor log form
    path('superuser/visitor-log/', visitor_log_list, name='visitor_log_list'),  # List of visitor logs
    path('user/visitor-log-list/', visitor_log_list_user, name='visitor_log_list_user'), 
    path('download/<int:log_id>/', download_visitor_log_pdf, name='download_visitor_log_pdf'),  # Download PDF
    path('superuser/visitor-log/<int:log_id>/delete/', delete_visitor_log, name='delete_visitor_log'),  # New URL for delete
    path('user/visitor-log/', visitor_log_user_view, name='visitor_log_user_view'),  # List of visitor logs

]

