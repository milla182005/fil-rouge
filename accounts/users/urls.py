from django.urls import path
from .views import RegisterView, UserDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'users'  # Permet de nommer les URLs et éviter les conflits

urlpatterns = [
    # Inscription
    path('register/', RegisterView.as_view(), name='register'),
    
    # Connexion / génération des tokens JWT
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Rafraîchissement du token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Lecture / modification / suppression du profil
    path('users/me/', UserDetailView.as_view(), name='user_detail'),
]
