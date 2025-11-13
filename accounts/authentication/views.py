from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

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


# -------------------------------
# Endpoint pour la déconnexion (Logout)
# -------------------------------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh", None)
        if not refresh_token:
            return Response({"error": "Refresh token non fourni."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # rend le refresh token invalide
            return Response({"message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Token invalide ou déjà blacklisté."}, status=status.HTTP_400_BAD_REQUEST)


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
