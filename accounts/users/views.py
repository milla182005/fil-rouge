from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer

# Endpoint pour l'inscription d'un utilisateur
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)  # Accessible à tous
    serializer_class = RegisterSerializer

# Endpoint pour voir, modifier ou supprimer le profil de l'utilisateur connecté
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)  # Authentification requise
    serializer_class = UserSerializer

    def get_object(self):
        """
        Retourne uniquement l'utilisateur actuellement connecté.
        """
        return self.request.user

    def delete(self, request, *args, **kwargs):
        """
        Supprime le compte de l'utilisateur connecté et renvoie un message de confirmation.
        """
        user = self.get_object()
        user.delete()
        return Response(
            {"detail": "Compte supprimé avec succès."},
            status=status.HTTP_204_NO_CONTENT
        )
