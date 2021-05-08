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
from django.contrib.auth import views as auth_views

from .views import (IndexView, NewsView, CoachesView, PricesView,
                    CourtsView, ArticlesView, ArticleDetailView, AccountView,
                    RegisterUserView, logout_user)

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('news/', NewsView.as_view(), name='news'),
    path('coaches/', CoachesView.as_view(), name='coaches'),
    path('prices/', PricesView.as_view(), name='prices'),
    path('courts/', CourtsView.as_view(), name='courts'),
    path('articles/', ArticlesView.as_view(), name='articles'),
    path(
        'articles/<slug:slug>/',
        ArticleDetailView.as_view(),
        name='article-detail',
    ),
    path('account/', AccountView.as_view(), name='account'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='volleyballschool/login.html',
        ),
        name='login',
    ),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('logout/', logout_user, name='logout'),
]
