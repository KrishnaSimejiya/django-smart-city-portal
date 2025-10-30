from django.urls import path, include
from .views import home, register, login, profile,logout,role,udashboard, password_reset_request, password_reset_confirm

urlpatterns = [
    path('',role,name='role'),
    path('home/',home,name='home'),
    path('register/',register,name='register'),
    path('login/',login,name='login'),
    path('udashboard/',udashboard,name='udashboard'),
    path('profile/',profile,name='profile'),
    path('logout/',logout, name='logout'),
    path('password-reset/', password_reset_request, name='password_reset_request'),
    path('password-reset/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
]