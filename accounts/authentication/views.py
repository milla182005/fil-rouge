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

# ==========================================
# REGISTER
# ==========================================
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: "Utilisateur créé", 400: "Erreur de validation"}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# ==========================================
# LOGIN
# ==========================================
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    @swagger_auto_schema(
        request_body=MyTokenObtainPairSerializer,
        responses={200: "Connexion réussie"}
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
                secure=False,
                samesite='Lax',
                max_age=60*60*24*7
            )
        return response


# ==========================================
# LOGOUT
# ==========================================
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization', openapi.IN_HEADER,
                description="Token JWT Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={205: "Déconnexion réussie", 400: "Refresh token manquant ou invalide"}
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token manquant."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response({"message": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('refresh_token')
            return response
        except Exception:
            return Response({"error": "Refresh token invalide."}, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# CHANGE PASSWORD
# ==========================================
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization', openapi.IN_HEADER,
                description="Token JWT Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ChangePasswordSerializer,
        responses={200: "Mot de passe changé", 400: "Erreur de validation"}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        user = request.user
        if serializer.is_valid():
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]
            if not user.check_password(old_password):
                return Response({"old_password": "Mot de passe incorrect."}, status=400)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Mot de passe changé."})
        return Response(serializer.errors, status=400)


# ==========================================
# BAN USER (ADMIN)
# ==========================================
class BanUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization', openapi.IN_HEADER,
                description="Token JWT Admin Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: "Utilisateur banni", 403: "Impossible de bannir un admin", 404: "Utilisateur non trouvé"}
    )
    def post(self, request, user_id):
        try:
            user_to_ban = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return Response({"error": "Utilisateur non trouvé."}, status=404)
        if user_to_ban.is_staff:
            return Response({"error": "Impossible de bannir un admin."}, status=403)
        user_to_ban.is_active = False
        user_to_ban.save()
        return Response({"message": f"L'utilisateur {user_to_ban.username} a été banni."})


# ==========================================
# REFRESH TOKEN
# ==========================================
class CookieTokenRefreshView(TokenRefreshView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"refresh": openapi.Schema(type=openapi.TYPE_STRING)},
            required=[]
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization', openapi.IN_HEADER,
                description="Token JWT (optionnel)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={200: "Token rafraîchi", 401: "Token invalide"}
    )
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        data = {"refresh": refresh} if refresh else {}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# ==========================================
# /auth/me — utilisateur connecté
# ==========================================
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization', openapi.IN_HEADER,
                description="Token JWT Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: "Informations de l'utilisateur connecté"}
    )
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_active": user.is_active,
        })


# ==========================================
# /auth/users — liste utilisateurs (ADMIN)
# ==========================================
class ListUsersView(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Token JWT Admin Bearer <token>",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: "Liste des utilisateurs"}
    )
    def list(self, request, *args, **kwargs):
        users = [{"id": u.id, "username": u.username, "email": u.email, "is_active": u.is_active}
                 for u in self.get_queryset()]
        return Response(users)
