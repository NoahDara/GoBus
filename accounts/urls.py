# accounts/urls.py - With Google OAuth

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Google OAuth
    path('google/auth/', views.GoogleAuthView.as_view(), name='google-auth'),
    path('google/callback/', views.GoogleAuthCallbackView.as_view(), name='google-callback'),
    
    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),
    path('password/change/', views.ChangePasswordView.as_view(), name='change-password'),
]