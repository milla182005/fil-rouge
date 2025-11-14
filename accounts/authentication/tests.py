from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
import json

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Création d'un admin et d'un utilisateur normal avec mots de passe conformes
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Admin1234!"
        )
        self.normal_user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="User1234!"
        )

    # -------------------------------
    # Test Register
    # -------------------------------
    def test_register_user(self):
        url = reverse("auth_register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "password2": "NewPass123!"
        }
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    # -------------------------------
    # Test Login
    # -------------------------------
    def test_login_user(self):
        url = reverse("auth_login")
        data = {"username": "user1", "password": "User1234!"}
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh_token", response.cookies)  # Le cookie doit être présent

    # -------------------------------
    # Test Logout
    # -------------------------------
    def test_logout_user(self):
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]
        self.client.cookies["refresh_token"] = login_resp.cookies.get("refresh_token").value

        logout_url = reverse("auth_logout")
        response = self.client.post(logout_url, HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        # Vérifie que le cookie refresh_token est vidé et supprimé
        self.assertEqual(response.cookies["refresh_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)

    # -------------------------------
    # Test Refresh Token
    # -------------------------------
    def test_refresh_token(self):
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        self.client.cookies["refresh_token"] = login_resp.cookies.get("refresh_token").value
        refresh_url = reverse("token_refresh")  # ✅ corrigé pour correspondre à urls.py
        response = self.client.post(refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    # -------------------------------
    # Test Change Password
    # -------------------------------
    def test_change_password(self):
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        url = reverse("auth_change_password")
        data = {"old_password": "User1234!", "new_password": "NewPass123!"}
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -------------------------------
    # Test Ban User by Admin
    # -------------------------------
    def test_ban_user_by_admin(self):
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "admin", "password": "Admin1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        url = reverse("ban_user", args=[self.normal_user.id])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    # -------------------------------
    # Test Ban User by Non-Admin
    # -------------------------------
    def test_ban_user_by_non_admin(self):
        login_resp = self.client.post(
            reverse("auth_login"),
            data=json.dumps({"username": "user1", "password": "User1234!"}),
            content_type="application/json"
        )
        access_token = login_resp.json()["access"]

        url = reverse("ban_user", args=[self.admin_user.id])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
