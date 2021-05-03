"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
"""
from django.urls import path

from .views import IndexView, NewsView, CoachesView

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('news/', NewsView.as_view(), name='news'),
    path('coaches/', CoachesView.as_view(), name='coaches'),
]
