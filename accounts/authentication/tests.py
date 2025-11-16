from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
import json


class AuthTests(TestCase):
    """Tests unitaires pour l'API d'authentification"""
    
    def setUp(self):
        """Configuration initiale avant chaque test"""
        self.client = Client()
        
        # Création d'un administrateur
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Admin1234!"
        )
        
        # Création d'un utilisateur normal
        self.normal_user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="User1234!"
        )

    # ========================================
    # TESTS D'INSCRIPTION (REGISTER)
    # ========================================
    
    def test_register_user_success(self):
        """Test d'inscription réussie avec des données valides"""
        url = reverse("auth_register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "password2": "NewPass123!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        
        # Vérifie que la réponse contient les données utilisateur
        response_data = response.json()
        self.assertIn("username", response_data)
        self.assertEqual(response_data["username"], "newuser")

    def test_register_password_mismatch(self):
        """Test d'inscription avec mots de passe différents"""
        url = reverse("auth_register")
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "password2": "DifferentPass123!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_register_duplicate_username(self):
        """Test d'inscription avec un nom d'utilisateur déjà existant"""
        url = reverse("auth_register")
        data = {
            "username": "user1",  # Déjà créé dans setUp
            "email": "duplicate@example.com",
            "password": "NewPass123!",
            "password2": "NewPass123!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========================================
    # TESTS DE CONNEXION (LOGIN)
    # ========================================
    
    def test_login_user_success(self):
        """Test de connexion réussie avec identifiants valides"""
        url = reverse("auth_login")
        data = {
            "username": "user1", 
            "password": "User1234!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh_token", response.cookies)

    def test_login_invalid_credentials(self):
        """Test de connexion avec des identifiants incorrects"""
        url = reverse("auth_login")
        data = {
            "username": "user1",
            "password": "WrongPassword!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test de connexion avec un utilisateur inexistant"""
        url = reverse("auth_login")
        data = {
            "username": "nonexistent",
            "password": "SomePass123!"
        }
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================
    # TESTS DE DÉCONNEXION (LOGOUT)
    # ========================================
    
    def test_logout_user_success(self):
        """Test de déconnexion réussie"""
        # Connexion préalable
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]
        self.client.cookies["refresh_token"] = login_resp.cookies.get("refresh_token").value

        # Déconnexion
        logout_url = reverse("auth_logout")
        response = self.client.post(
            logout_url, 
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.cookies["refresh_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)

    def test_logout_without_authentication(self):
        """Test de déconnexion sans être authentifié"""
        logout_url = reverse("auth_logout")
        response = self.client.post(logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================
    # TESTS DE REFRESH TOKEN
    # ========================================
    
    def test_refresh_token_success(self):
        """Test de rafraîchissement du token avec un refresh token valide"""
        # Connexion pour obtenir un refresh token
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        self.client.cookies["refresh_token"] = login_resp.cookies.get("refresh_token").value
        
        # Rafraîchissement
        refresh_url = reverse("token_refresh")
        response = self.client.post(refresh_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    def test_refresh_token_without_cookie(self):
        """Test de rafraîchissement sans refresh token"""
        refresh_url = reverse("token_refresh")
        response = self.client.post(refresh_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========================================
    # TESTS DE CHANGEMENT DE MOT DE PASSE
    # ========================================
    
    def test_change_password_success(self):
        """Test de changement de mot de passe réussi"""
        # Connexion
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Changement de mot de passe
        url = reverse("auth_change_password")
        data = {
            "old_password": "User1234!", 
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!"
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le nouveau mot de passe fonctionne
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.check_password("NewPass123!"))

    def test_change_password_wrong_old_password(self):
        """Test de changement de mot de passe avec ancien mot de passe incorrect"""
        # Connexion
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Changement avec mauvais ancien mot de passe
        url = reverse("auth_change_password")
        data = {
            "old_password": "WrongOldPass!", 
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!"
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_authentication(self):
        """Test de changement de mot de passe sans authentification"""
        url = reverse("auth_change_password")
        data = {
            "old_password": "User1234!", 
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!"
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================
    # TESTS DE BANNISSEMENT D'UTILISATEURS
    # ========================================
    
    def test_ban_user_by_admin_success(self):
        """Test de bannissement d'un utilisateur par un administrateur"""
        # Connexion admin
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "admin", "password": "Admin1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Bannissement
        url = reverse("ban_user", args=[self.normal_user.id])
        response = self.client.post(
            url, 
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    def test_ban_user_by_non_admin_forbidden(self):
        """Test de bannissement par un utilisateur normal (doit échouer)"""
        # Connexion utilisateur normal
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Tentative de bannissement
        url = reverse("ban_user", args=[self.admin_user.id])
        response = self.client.post(
            url, 
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ban_nonexistent_user(self):
        """Test de bannissement d'un utilisateur inexistant"""
        # Connexion admin
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "admin", "password": "Admin1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Tentative de bannissement d'un ID inexistant
        url = reverse("ban_user", args=[99999])
        response = self.client.post(
            url, 
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ban_admin_user_forbidden(self):
        """Test de bannissement d'un administrateur (doit échouer)"""
        # Créer un second admin
        admin2 = User.objects.create_superuser(
            username="admin2",
            email="admin2@example.com",
            password="Admin1234!"
        )
        
        # Connexion du premier admin
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "admin", "password": "Admin1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        # Tentative de bannissement de l'autre admin
        url = reverse("ban_user", args=[admin2.id])
        response = self.client.post(
            url, 
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)