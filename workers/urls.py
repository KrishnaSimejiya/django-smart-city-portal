from django.urls import path, include
from .views import whome, wregister, wlogin, wprofile, wdashboard, new_work, update_complaint_status, completed_complaints, wpassword_reset_request, wpassword_reset_confirm

urlpatterns = [
    path('whome/',whome,name='whome'),
    path('wregister/',wregister,name='wregister'),
    path('wlogin/',wlogin,name='wlogin'),
    path('wprofile/',wprofile,name='wprofile'),
    path('wdashboard/', wdashboard, name='wdashboard'),
    path('new-work/', new_work, name='new_work'),
    path('complaint/<int:complaint_id>/update-status/', update_complaint_status, name='worker_update_status'),
    path('completed/', completed_complaints, name='completed_complaints'),
    path('password-reset/', wpassword_reset_request, name='wpassword_reset_request'),
    path('password-reset/<str:token>/', wpassword_reset_confirm, name='wpassword_reset_confirm'),
]