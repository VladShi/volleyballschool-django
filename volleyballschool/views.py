from django.views.generic import ListView, TemplateView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .models import (
    News, Coach, SubscriptionSample, OneTimeTraining, Court, Article,
)
from .forms import RegisterUserForm


class IndexView(ListView):

    template_name = 'volleyballschool/index.html'
    context_object_name = 'latest_news_list'
    queryset = News.objects.order_by('-date')[:3]


class NewsView(ListView):

    model = News
    paginate_by = 4
    template_name = 'volleyballschool/news.html'
    context_object_name = 'news_list'


class CoachesView(ListView):

    queryset = Coach.objects.filter(active=True)
    template_name = 'volleyballschool/coaches.html'
    context_object_name = 'coaches_list'


class PricesView(TemplateView):

    template_name = 'volleyballschool/prices.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription_samples'] = SubscriptionSample.objects.filter(
            active=True)
        context['one_time_training'] = OneTimeTraining.objects.first()
        return context


class CourtsView(ListView):

    template_name = 'volleyballschool/courts.html'
    queryset = Court.objects.filter(
        active=True).values_list('metro', flat=True)
    context_object_name = 'courts_metro_list'


class ArticlesView(ListView):

    queryset = Article.objects.filter(active=True)
    template_name = 'volleyballschool/articles.html'
    context_object_name = 'articles_list'
    paginate_by = 5


class ArticleDetailView(DetailView):

    model = Article
    context_object_name = 'article'


class AccountView(LoginRequiredMixin, TemplateView):

    template_name = 'volleyballschool/account.html'
    login_url = 'login'


class RegisterUserView(CreateView):

    form_class = RegisterUserForm
    template_name = "volleyballschool/register.html"
    success_url = reverse_lazy('account')


def logout_user(request):
    logout(request)
    return redirect('login')
