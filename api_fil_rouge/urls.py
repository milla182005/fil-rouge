"""
URL configuration for api_fil_rouge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('accounts.users.urls')),
    path('api/auth/', include('accounts.authentication.urls')),
]
