from django.urls import path
from .views import (
    RegisterView,
    MyTokenObtainPairView,
    LogoutView,
    ChangePasswordView,
    BanUserView,
    CookieTokenRefreshView,
    MeView,
    ListUsersView,
    WeatherView 
)

urlpatterns = [
    # -------------------------------
    # Auth endpoints
    # -------------------------------
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', MyTokenObtainPairView.as_view(), name='auth_login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),

    path('me/', MeView.as_view(), name='auth_me'),
    path('users/', ListUsersView.as_view(), name='auth_users'),
    path('weather/<str:city>/', WeatherView.as_view(), name='weather'),

    # -------------------------------
    # Admin only
    # -------------------------------
    path('ban-user/<int:user_id>/', BanUserView.as_view(), name='ban_user'),
]
