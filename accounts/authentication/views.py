from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, ChangePasswordSerializer


# -------------------------------
# Endpoint pour l'inscription
# -------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# -------------------------------
# Endpoint pour la connexion (JWT)
# -------------------------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Récupère le refresh token de la réponse
        refresh_token = response.data.get('refresh')
        
        if refresh_token:
            # Supprime le refresh token du body JSON
            response.data.pop('refresh')
            
            # Stocke le refresh token dans un cookie HTTP-only sécurisé
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,  # Inaccessible via JavaScript
                secure=False,   # True en production (HTTPS uniquement)
                samesite='Lax', # Protection CSRF
                max_age=60*60*24*7  # 7 jours
            )
        
        return response


# -------------------------------
# Endpoint pour la déconnexion (Logout)
# -------------------------------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Récupère le refresh token depuis le cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {"error": "Refresh token non trouvé."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Crée la réponse
            response = Response(
                {"message": "Déconnexion réussie."}, 
                status=status.HTTP_205_RESET_CONTENT
            )
            
            # Supprime le cookie
            response.delete_cookie('refresh_token')
            
            return response
            
        except Exception as e:
            return Response(
                {"error": "Token invalide ou déjà blacklisté."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

# -------------------------------
# Endpoint pour changer le mot de passe
# -------------------------------
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user

        if serializer.is_valid():
            old_password = serializer.validated_data.get("old_password")
            new_password = serializer.validated_data.get("new_password")

            if not user.check_password(old_password):
                return Response({"old_password": "Mot de passe actuel incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"message": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Endpoint pour bannir un utilisateur (RBAC : Admin seulement)
# -------------------------------
class BanUserView(APIView):
    permission_classes = [permissions.IsAdminUser]  # Seuls les admins peuvent accéder

    def post(self, request, user_id):
        try:
            user_to_ban = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return Response({"error": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if user_to_ban.is_staff:
            return Response({"error": "Impossible de bannir un administrateur."}, status=status.HTTP_403_FORBIDDEN)

        user_to_ban.is_active = False  # Désactive le compte
        user_to_ban.save()
        return Response(
            {"message": f"L'utilisateur {user_to_ban.username} a été banni par {request.user.username}."},
            status=status.HTTP_200_OK
        )


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Récupère le refresh token depuis le cookie
        refresh_token = request.COOKIES.get('refresh_token')
        
        data = {}
        if refresh_token:
            data['refresh'] = refresh_token

        # Appelle la vue parent avec un dictionnaire mutable
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
