from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/callback/', views.auth_callback_view, name='auth_callback'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
]
