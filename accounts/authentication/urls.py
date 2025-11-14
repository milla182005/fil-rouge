from django.urls import path
from .views import (
    RegisterView,
    MyTokenObtainPairView,
    LogoutView,
    ChangePasswordView,
    BanUserView,
    CookieTokenRefreshView,
    MeView,
    ListUsersView 
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [

    # -------------------------------
    # Endpoints Authentification
    # -------------------------------
    path('register/', RegisterView.as_view(), name='auth_register'),           # Inscription
    path('login/', MyTokenObtainPairView.as_view(), name='auth_login'),        # Connexion (JWT)
    path('logout/', LogoutView.as_view(), name='auth_logout'),                 # Déconnexion
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),  # Refresh token
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),  # Changement de mot de passe

    path("me/", MeView.as_view(), name="auth_me"),
    path("users/", ListUsersView.as_view(), name="auth_users"),

    # -------------------------------
    # Endpoint RBAC : admin uniquement
    # -------------------------------
    path('ban-user/<int:user_id>/', BanUserView.as_view(), name='ban_user'),   # Bannir un utilisateur
]
