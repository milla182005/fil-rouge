from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        ref_name = 'UserRegister'  # Nom unique pour Swagger
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        """
        Crée un utilisateur avec mot de passe haché.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
