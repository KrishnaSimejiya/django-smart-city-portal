from django.urls import path, include
from .views import dashboard,all_users,all_workers,delete_user,reset_password,admin_login,new_complaints,assign_work,all_services

urlpatterns = [
    path('dashboard/',dashboard,name='dashboard'),
    path('all_users/',all_users,name='all_users'),
    path('all_workers/',all_workers,name='all_workers'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('reset_password/<int:user_id>/', reset_password, name='reset_password'),
    path('admin-login/',admin_login,name='admin_login'),
    path('new-complaints/', new_complaints, name='new_complaints'),
    path('assign-work/<int:complaint_id>/', assign_work, name='assign_work'),
    path('all-services/', all_services, name='all_services'),
]