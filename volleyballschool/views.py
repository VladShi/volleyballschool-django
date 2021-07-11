import datetime

from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DetailView, ListView,
                                  TemplateView, View)

from volleyballschool.utils import (cancel_registration_for_training,
                                    copy_same_fields,
                                    get_start_date_and_end_date,
                                    transform_for_timetable)

from .forms import RegisterUserForm
from .models import (Article, Coach, Court, News, OneTimeTraining,
                     Subscription, SubscriptionSample, Training, User)


class IndexView(ListView):

    template_name = 'volleyballschool/index.html'
    context_object_name = 'latest_news_list'
    queryset = News.objects.order_by('-date')[:3]


class LevelsView(TemplateView):

    template_name = 'volleyballschool/levels.html'


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


class BuyingASubscriptionView(LoginRequiredMixin, DetailView):

    template_name = 'volleyballschool/buying-a-subscription.html'
    context_object_name = 'subscription_sample'

    def get_object(self):
        subscription_sample = get_object_or_404(
            SubscriptionSample,
            pk=self.kwargs['pk'],
            active=True,
        )
        return subscription_sample

    def post(self, request, *args, **kwargs):
        if request.POST.get('confirm', False):
            subscription_sample = self.get_object()
            if request.user.balance > subscription_sample.amount:
                subscription = Subscription()
                copy_same_fields(subscription_sample, subscription)
                subscription.user = request.user
                subscription.purchase_date = datetime.date.today()
                subscription.save()
                request.user.balance -= subscription_sample.amount
                request.user.save(update_fields=['balance'])
                request.session['submitted'] = True
                return redirect(
                    'success-buying-a-subscription', subscription.id
                )
        return redirect('buying-a-subscription', self.kwargs['pk'])


class SuccessBuyingASubscriptionView(LoginRequiredMixin, View):

    template_name = 'volleyballschool/success-buying-a-subscription.html'

    def get(self, request, *args, **kwargs):
        if request.session.get('submitted', False):
            subscription = get_object_or_404(
                Subscription.objects.select_related('user'),
                pk=self.kwargs['pk'],
            )
            request.session.pop('submitted', None)
            return render(
                request, self.template_name, {'subscription': subscription}
            )
        return redirect('prices')


class RegistrationForTrainingView(LoginRequiredMixin, DetailView):

    template_name = 'volleyballschool/registration-for-training.html'
    context_object_name = 'training'

    def get_object(self):
        training = Training.get_upcoming_training_or_404(self.kwargs['pk'])
        return training

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user in self.object.learners.all():
            context['already_registered'] = True
        training_date = self.object.date
        context['subscription_of_user'] = user.get_first_active_subscription(
            training_date,
            check_zero_qty=True
        )
        context['price_for_one_training'] = (
                        OneTimeTraining.objects.first().price
                    )
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        training = Training.get_upcoming_training_or_404(self.kwargs['pk'])
        if request.POST.get('confirm', False):
            # запись на тренировку
            if training.get_free_places() > 0:
                if request.POST.get('payment_by', False) == 'subscription':
                    subscription_of_user = (
                        user.get_first_active_subscription(
                            training.date,
                            check_zero_qty=True
                        )
                    )
                    if subscription_of_user:
                        training.learners.add(user)
                        subscription_of_user.trainings.add(training)
                if request.POST.get('payment_by', False) == 'balance':
                    price_for_one_training = (
                        OneTimeTraining.objects.first().price
                    )
                    if user.balance > price_for_one_training:
                        training.learners.add(user)
                        user.balance -= price_for_one_training
                        user.save(update_fields=['balance'])
            return redirect('registration-for-training', self.kwargs['pk'])
        if request.POST.get('cancel', False):
            price_for_one_training = (OneTimeTraining.objects.first().price)
            cancel_registration_for_training(user, training,
                                             price_for_one_training)
        return redirect('registration-for-training', self.kwargs['pk'])


class AccountView(LoginRequiredMixin, TemplateView):

    template_name = 'volleyballschool/account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year_ago = datetime.date.today() - datetime.timedelta(days=365)
        last_year_subscriptions = (
            Subscription.objects.prefetch_related('trainings').filter(
                purchase_date__gte=year_ago).order_by('purchase_date')
        )
        prefetch_subscriptions = Prefetch(
            'subscriptions', queryset=last_year_subscriptions)
        upcoming_trainings = Training.objects.select_related(
            'court').filter(date__gte=datetime.date.today())
        prefetch_trainings = Prefetch(
            'trainings', queryset=upcoming_trainings)
        user_pk = self.request.user.pk
        user = User.objects.prefetch_related(
            prefetch_trainings, prefetch_subscriptions).get(pk=user_pk)
        user_upcoming_trainings = user.trainings.all()
        context['user_upcoming_trainings'] = user_upcoming_trainings
        user_last_year_subscriptions = user.subscriptions.all()[:3]
        user_active_subscriptions = []
        last_not_active_subscription = None
        for subscription in user_last_year_subscriptions:
            if subscription.is_active():
                user_active_subscriptions.append(subscription)
            else:
                last_not_active_subscription = subscription
        context['user_active_subscriptions'] = user_active_subscriptions
        context['last_not_active_subscription'] = last_not_active_subscription
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('cancel', False):
            training = Training.get_upcoming_training_or_404(
                request.POST.get('pk', None))
            price_for_one_training = (OneTimeTraining.objects.first().price)
            cancel_registration_for_training(request.user, training,
                                             price_for_one_training)
        return redirect('account')


class RegisterUserView(CreateView):

    form_class = RegisterUserForm
    template_name = "volleyballschool/register.html"
    success_url = reverse_lazy('account')


def logout_user(request):
    logout(request)
    return redirect('login')
