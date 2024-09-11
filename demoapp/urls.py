# complaint/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.redirect_to_home),  # Redirect root URL to /home/
    path('home/', views.home_page, name='home'),
    path('superuser/signup/', views.signup_view, name='signup'),
    path('user/login/', views.login_view, name='login'),  
    path('superuser/login/',views.login1_view,name="login1"),
    path('superuser/services/', views.admin_page, name='admin'),
    path('user/services/', views.user_page, name='user'),
    path('user/newcomplaint/', views.complaint_form, name='complaint_form'),
    path('user/DGR/', views.generate_word1, name='generate_word'),
    path('superuser/DGR/', views.generate_word, name='generate_word1'),
    path('user/new/', views.complaint_form, name='new_complaint'),
    path('user/history/', views.final_complaints_user, name='final_complaints_user'),
    path('superuser/approval/', views.approval_complaints, name='approval_complaints'),
    path('superuser/approve_complaint/<int:complaint_id>/', views.accept_complaint, name='accept_complaint'),
    path('user/existing/', views.existing_complaints, name='existing_complaints'),
    path('user/edit/<int:complaint_id>/', views.edit_complaint, name='edit_complaint'),
    path('superuser/history/', views.final_complaints, name='final_complaints'),
    path('delete_complaint/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
    path('complaint_analysis/', views.complaint_analysis, name='complaint_analysis'),
]
