from django.shortcuts import render
from django.views.generic import ListView

from .models import News

# Create your views here.

class IndexView(ListView):
    template_name = 'volleyballschool/index.html'
    context_object_name = 'latest_news_list'
    queryset = News.objects.order_by('-date')[:3]

class News(ListView):
    model = News
    paginate_by = 4
    template_name = 'volleyballschool/news.html'
    context_object_name = 'news_list'
    