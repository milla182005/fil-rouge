from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    RegisterSerializer, 
    MyTokenObtainPairSerializer, 
    ChangePasswordSerializer
)


# -------------------------------
# Endpoint pour l'inscription
# -------------------------------
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Utilisateur créé avec succès",
                examples={"application/json": {"username": "newuser", "email": "newuser@example.com"}}
            ),
            400: "Erreur de validation"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# -------------------------------
# Endpoint pour la connexion (JWT)
# -------------------------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        request_body=MyTokenObtainPairSerializer,
        responses={
            200: openapi.Response(
                description="Connexion réussie",
                examples={"application/json": {"access": "jwt_token_here"}}
            ),
            401: "Échec d'authentification"
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')

        if refresh_token:
            response.data.pop('refresh')
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=False,  # True en production
                samesite='Lax',
                max_age=60*60*24*7
            )
        return response


# -------------------------------
# Endpoint pour la déconnexion (Logout)
# -------------------------------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            205: "Déconnexion réussie",
            400: "Refresh token manquant ou invalide"
        }
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token non trouvé."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response({"message": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('refresh_token')
            return response
        except Exception:
            return Response({"error": "Token invalide ou déjà blacklisté."}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Endpoint pour changer le mot de passe
# -------------------------------
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Mot de passe changé avec succès",
                examples={"application/json": {"message": "Mot de passe changé avec succès."}}
            ),
            400: openapi.Response(
                description="Ancien mot de passe incorrect ou validation échouée",
                examples={"application/json": {"old_password": "Mot de passe actuel incorrect."}}
            )
        }
    )
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
# Endpoint pour bannir un utilisateur (Admin seulement)
# -------------------------------
class BanUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        responses={
            200: "Utilisateur banni avec succès",
            403: "Impossible de bannir un administrateur ou accès refusé",
            404: "Utilisateur non trouvé"
        }
    )
    def post(self, request, user_id):
        try:
            user_to_ban = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return Response({"error": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if user_to_ban.is_staff:
            return Response({"error": "Impossible de bannir un administrateur."}, status=status.HTTP_403_FORBIDDEN)

        user_to_ban.is_active = False
        user_to_ban.save()
        return Response({"message": f"L'utilisateur {user_to_ban.username} a été banni par {request.user.username}."}, status=status.HTTP_200_OK)


# -------------------------------
# Refresh token depuis cookie
# -------------------------------
class CookieTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        responses={
            200: "Token rafraîchi avec succès",
            401: "Refresh token invalide"
        }
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        data = {}
        if refresh_token:
            data['refresh'] = refresh_token
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
