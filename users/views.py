from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer

# Endpoint pour s’inscrire
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)  # Public
    serializer_class = RegisterSerializer

# Endpoint pour voir ou modifier son profil
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)  # Auth uniquement
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
