from django.urls import path, include
from .views import create_request,request_list, track_status

urlpatterns = [
    path('create_request/',create_request,name='create_request'),
    path('request_list/',request_list,name='request_list'),
    path('track_status/', track_status, name='track_status'),
]