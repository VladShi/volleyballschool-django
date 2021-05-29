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
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from .views import (AccountView, ArticleDetailView, ArticlesView,
                    BuyingASubscriptionView, CancelRegistrationForTrainingView,
                    CoachesView, ConfirmRegistrationForTrainingView,
                    CourtsView, IndexView, NewsView, PricesView,
                    RegisterUserView, RegistrationForTrainingView,
                    SuccessBuyingASubscriptionView, TimetableView, logout_user)

urlpatterns = [
    path('', IndexView.as_view(), name='index_page'),
    path('news/', NewsView.as_view(), name='news'),
    path('Coaches/', CoachesView.as_view(), name='coaches'),
    path('prices/', PricesView.as_view(), name='prices'),
    path('courts/', CourtsView.as_view(), name='courts'),
    path('articles/', ArticlesView.as_view(), name='articles'),
    path(
        'articles/<slug:slug>/',
        ArticleDetailView.as_view(),
        name='article-detail',
    ),
    re_path(
        r'^timetable/(?P<skill_level>[1-3]{1})/$',
        TimetableView.as_view(),
        name='timetable'
    ),
    path(
        'buying-a-subscription/<int:pk>/',
        BuyingASubscriptionView.as_view(),
        name='buying-a-subscription',
    ),
    path(
        'success-buying-a-subscription/<int:pk>/',
        SuccessBuyingASubscriptionView.as_view(),
        name='success-buying-a-subscription',
    ),
    path(
        'registration-for-training/<int:pk>/',
        RegistrationForTrainingView.as_view(),
        name='registration-for-training',
    ),
    path(
        'confirm-registration-for-training/<int:pk>/',
        ConfirmRegistrationForTrainingView.as_view(),
        name='confirm-registration-for-training',
    ),
    path(
        'cancel-registration-for-training/<int:pk>/',
        CancelRegistrationForTrainingView.as_view(),
        name='cancel-registration-for-training',
    ),
    path('account/', AccountView.as_view(), name='account'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='volleyballschool/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('logout/', logout_user, name='logout'),
]
