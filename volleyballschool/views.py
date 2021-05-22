import datetime

from django.views.generic import (
    ListView, TemplateView, DetailView, CreateView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .models import (
    News, Coach, SubscriptionSample, OneTimeTraining, Court, Article, Training,
)
from .forms import RegisterUserForm
from volleyballschool.utils import (
    get_start_date_and_end_date, transform_for_timetable,
)


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


class TimetableView(ListView):

    template_name = 'volleyballschool/timetable.html'
    context_object_name = 'trainings'

    def get_queryset(self):
        number_of_weeks = 2
        start_date, end_date = get_start_date_and_end_date(number_of_weeks)
        query_set = Training.objects.select_related('court', 'coach').filter(
            skill_level=int(self.kwargs['skill_level']),
            date__gte=start_date,
            date__lte=end_date,
            active=True,
        )
        transformed_query_set = transform_for_timetable(
            query_set=query_set,
            start_date=start_date,
            number_of_weeks=number_of_weeks,
        )
        return transformed_query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        skill_level_selector = int(self.kwargs['skill_level'])
        skill_levels_list = {
            1: 'для начального уровня',
            2: 'для уровня начальный+',
            3: 'для среднего уровня',
        }
        context['skill_level'] = skill_levels_list[skill_level_selector]
        context['datetime_now'] = datetime.datetime.now()
        return context


class RegistrationForTrainingView(DetailView):

    template_name = 'volleyballschool/registration-for-training.html'
    context_object_name = 'training'

    def get_object(self):
        training = Training.get_upcoming_training_or_404(self.kwargs['pk'])
        return training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user in self.object.learners.all():
            context['already_registered'] = True
        return context


class ConfirmRegistrationForTrainingView(View):

    def get(self, request, *args, **kwargs):
        training = Training.get_upcoming_training_or_404(self.kwargs['pk'])
        if training.get_free_places() > 0:
            training.learners.add(request.user)
        return redirect('registration-for-training', self.kwargs['pk'])


class CancelRegistrationForTrainingView(View):

    def get(self, request, *args, **kwargs):
        training = Training.get_upcoming_training_or_404(self.kwargs['pk'])
        if (
            self.request.user in training.learners.all()
            and training.is_more_than_an_hour_before_start()
        ):
            training.learners.remove(request.user)
        return redirect('registration-for-training', self.kwargs['pk'])


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
