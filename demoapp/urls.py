from django.urls import path
from . import views
# from gatepass.views import visitor_log_view, visitor_log_list, download_visitor_log_pdf, delete_visitor_log,visitor_log_user_view, visitor_log_list_user
from .views import CustomLogoutView

urlpatterns = [
    path('', views.redirect_to_home),  
    path('home/', views.home_page, name='home'),
    path('superuser/signup/', views.signup_view, name='signup'),
    path('user/login/', views.user_login_view, name='login'),  
    path('superuser/login/',views.admin_login_view,name="login1"),
    path('superuser/services/', views.admin_page, name='admin'),
    path('user/services/', views.user_page, name='user'),
    path('user/new/', views.complaint_form, name='complaint_form'),
    path('user/history/', views.final_complaints_user, name='final_complaints_user'),
    path('superuser/approval/', views.approval_complaints, name='approval_complaints'),
    path('superuser/approve_complaint/<int:complaint_id>/', views.accept_complaint, name='accept_complaint'),
    path('user/existing/', views.existing_complaints, name='existing_complaints'),
    path('user/edit/<int:complaint_id>/', views.edit_complaint, name='edit_complaint'),
    path('superuser/history/', views.final_complaints, name='final_complaints'),
    path('delete_complaint/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('superuser/complaint_analysis/', views.complaint_analysis, name='complaint_analysis'),
    path('complaints/<str:type>/<str:site_name>/', views.ComplaintDetailView, name='complaints_detail'), 
    path('reject_complaint/', views.rejected_complaints, name='rejected_complaints'),
    path('export_complaints/<str:type>/<str:site_name>/', views.export_complaints_to_csv, name='export_complaints_to_csv'),  
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('delete_user_complaint/<int:complaint_id>/', views.delete_user_complaint, name='delete_user_complaint'),
]
