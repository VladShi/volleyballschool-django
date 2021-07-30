import datetime

from ckeditor_uploader.fields import RichTextUploadingField

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from .utils import (
    create_trainings_based_on_timeteble_for_x_days, copy_same_fields,
    get_upcoming_training_or_404
)


class User(AbstractUser):
    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    balance = models.DecimalField(
        verbose_name='Баланс (руб.)',
        max_digits=9,
        decimal_places=2,
        default=0,
    )
    passport_number = models.CharField(
        verbose_name='Номер паспорта',
        max_length=15,
        blank=True,
    )
    passport_data = models.CharField(
        verbose_name='Паспортные данные',
        max_length=195,
        blank=True,
    )

    def get_first_active_subscription(self, training_date):
        """returns first by purchase_date active subscription with not null
        remaining trainings of user valid for upcoming training_date or None.

        Args:
            training_date (datetime.date):
                date for which the subscription activity is checked.
        """
        subscriptions = list(
            self.subscriptions.filter(active=True).order_by('purchase_date')
        )
        for subscription in subscriptions:
            subscription_is_active, remaining_trainings_qty = (
                subscription.is_active(return_qty=True)
            )
            subscription_end_date = subscription.get_end_date()
            if (
                subscription_is_active
                and training_date >= datetime.date.today()
                and subscription_end_date >= training_date
                and remaining_trainings_qty > 0
            ):
                return subscription


class News(models.Model):
    title = models.CharField('Заголовок', max_length=120)
    date = models.DateField('Дата', auto_now_add=True)
    text = models.TextField('Текст', blank=True)
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='news_images/',
        blank=True,
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'

    def __str__(self):
        return self.title[:30] + '...'


class Coach(models.Model):
    name = models.CharField('Имя', max_length=100)
    description = models.TextField('Описание')
    photo = models.ImageField(
        verbose_name='Фото',
        upload_to='photos_of_coaches/',
        blank=True,
    )
    active = models.BooleanField('Активный')

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'

    def __str__(self):
        return self.name


class SubscriptionSample(models.Model):
    """Шаблон Абонемента"""

    name = models.CharField('Наименование', max_length=80)
    amount = models.PositiveIntegerField('Стоимость(руб.)')
    trainings_qty = models.PositiveSmallIntegerField('Количество тренировок')
    validity = models.PositiveSmallIntegerField('Срок действия(дней)')
    active = models.BooleanField('Активный')

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'

    def __str__(self):
        return self.name

    def clean(self):
        if self.trainings_qty == 0:
            raise ValidationError({
                'trainings_qty': ValidationError(
                    ('количество тренировок не должно быть равным нулю'),
                    code='invalid'
                ),
            })

    def get_price_for_one_training(self):
        try:
            return int(self.amount / self.trainings_qty)
        except ZeroDivisionError:
            return "количество тренировок не должно быть равным нулю"


class Subscription(models.Model):
    trainings_qty = models.PositiveSmallIntegerField('Количество тренировок')
    validity = models.PositiveSmallIntegerField('Срок действия(дней)')
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    purchase_date = models.DateField('Дата покупки', auto_now_add=True)
    trainings = models.ManyToManyField(
        'Training',
        verbose_name='Тренировки',
        blank=True,
    )
    start_date = models.DateField(
        verbose_name='Дата начала действия',
        blank=True,
        null=True,
    )
    end_date = models.DateField(
        verbose_name='Дата окончания действия',
        blank=True,
        null=True,
    )
    active = models.BooleanField('Активный', default=True)

    class Meta:
        verbose_name = 'Абонемент пользователя'
        verbose_name_plural = 'Абонементы пользователей'

    def __str__(self):
        return (
            'Абонемент пользователя {}, дата покупки {}'.format(
                self.user,
                self.purchase_date,
            )
        )

    def get_start_date(self):
        """Дата отсчёта срока действия абонемента.
        Отсчёт с момента первого посещения тренировки, но не позднее чем через
        10 дней с момента покупки.
        Returns:
            [datetime.date]
        """
        if self.start_date:
            return self.start_date
        first_training = self.trainings.order_by('date').first()
        ten_days_from_purchase = (self.purchase_date
                                  + datetime.timedelta(days=10))
        validity = datetime.timedelta(days=self.validity)
        if first_training and first_training.date <= ten_days_from_purchase:
            if datetime.date.today() > first_training.date:
                self.start_date = first_training.date
                self.end_date = self.start_date + validity
                self.save(update_fields=['start_date', 'end_date'])
            return first_training.date
        if datetime.date.today() > ten_days_from_purchase:
            self.start_date = self.purchase_date
            self.end_date = self.start_date + validity
            self.save(update_fields=['start_date', 'end_date'])
        return self.purchase_date

    def get_end_date(self):
        if self.end_date:
            return self.end_date
        validity = datetime.timedelta(days=self.validity)
        if self.start_date:
            self.end_date = self.start_date + validity
            self.save(update_fields=['end_date'])
            return self.end_date
        return self.purchase_date + validity

    def get_remaining_trainings_qty(self):
        return self.trainings_qty - self.trainings.count()

    def is_active(self, return_qty=False):
        if self.active is False:
            if return_qty is False:
                return False
            return False, self.get_remaining_trainings_qty()
        if datetime.date.today() > self.get_end_date():
            self.active = False
            self.save(update_fields=['active'])
            if return_qty is False:
                return False
            return False, self.get_remaining_trainings_qty()
        remaining_trainings_qty = self.get_remaining_trainings_qty()
        if remaining_trainings_qty <= 0:
            last_training = self.trainings.order_by('date').last()
            if datetime.date.today() > last_training.date:
                self.active = False
                self.save(update_fields=['active'])
                if return_qty is False:
                    return False
                return False, remaining_trainings_qty
        if return_qty is False:
            return True
        return True, remaining_trainings_qty


class OneTimeTraining(models.Model):
    """В таблице должна находиться только единственная запись с ценной
    за разовое занятие. В админке отключаем возможность добавления
    больше одной записи в модель.
    """

    price = models.PositiveSmallIntegerField('Цена(руб.)')

    class Meta:
        verbose_name = 'Стоимость разового занятия'
        verbose_name_plural = 'Стоимость разового занятия'

    def __str__(self):
        return 'Изменить стоимость разового занятия'

    def save(self, *args, **kwargs):
        if OneTimeTraining.objects.first():
            return
        super().save(*args, **kwargs)


class Court(models.Model):
    """Волейбольные залы"""

    name = models.CharField('Наименование', max_length=120)
    description = models.TextField('Описание', blank=True)
    address = models.CharField('Адрес', max_length=120)
    metro = models.CharField('Станция метро', max_length=50)
    photo = models.ImageField(
        verbose_name='Фото',
        upload_to='photos_of_courts/',
        blank=True,
    )
    longitude = models.DecimalField(
        verbose_name='Долгота',
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(
        verbose_name='Широта',
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )
    passport_required = models.BooleanField('Требуется паспорт')
    active = models.BooleanField('Активный')

    class Meta:
        verbose_name = 'Зал'
        verbose_name_plural = 'Залы'

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField('Заголовок', max_length=180)
    slug = models.SlugField(
        verbose_name='Slug( URL )',
        max_length=200,
        unique=True,
    )
    short_description = models.TextField(
        verbose_name='Краткое описание статьи',
        max_length=400,
    )
    text = RichTextUploadingField('Текст')
    active = models.BooleanField('Активна')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title[:40] + '...'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article-detail', args=[str(self.slug)])


class TimetableSample(models.Model):
    """Абстрактная модель. Шаблон, список общих полей для стандартного
    расписания(Timetable) и отдельных тренировок(Trainings), которые имеют
    много одинаковых полей.
    Добавляйте поля, которые будут присутствовать и в расписании и в отдельных
    тренировках в эту модель.
    """

    class DaysOfTheWeek(models.IntegerChoices):
        MONDAY = 1, 'Понедельник'
        TUESDAY = 2, 'Вторник'
        WEDNESDAY = 3, 'Среда'
        THURSDAY = 4, 'Четверг'
        FRIDAY = 5, 'Пятница'
        SATURDAY = 6, 'Суббота'
        SUNDAY = 7, 'Воскресенье'

    class SkillLevels(models.IntegerChoices):
        BEGGINER = 1, 'начальный уровень'
        BEGGINER_PLUS = 2, 'уровень начальный+'
        MIDDLE = 3, 'средний уровень'

    day_of_week = models.SmallIntegerField(
        verbose_name='день недели',
        choices=DaysOfTheWeek.choices,
    )
    skill_level = models.SmallIntegerField(
        verbose_name='уровень',
        choices=SkillLevels.choices,
    )
    court = models.ForeignKey(
        Court,
        verbose_name='зал',
        on_delete=models.CASCADE,
        limit_choices_to={'active': True},
    )
    coach = models.ForeignKey(
        Coach,
        verbose_name='тренер',
        on_delete=models.SET_DEFAULT,
        default=None,
        blank=True,
        null=True,
    )
    start_time = models.TimeField('время начала')
    active = models.BooleanField('активно', default=True)

    class Meta:
        abstract = True


class Timetable(TimetableSample):

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'

    def __str__(self):
        return (
            '{} {} {}'.format(
                self.get_skill_level_display().title(),
                self.court,
                self.get_day_of_week_display()
            )
        )

    def save(self, *args, **kwargs):
        if self.id:  # если расписание уже создано ранее
            matching_trainings = Training.objects.filter(
                date__gte=datetime.date.today(),
                skill_level=self.skill_level,
                court=self.court,
                day_of_week=self.day_of_week,
                status=1,
            )
            if self.active is True and matching_trainings:
                for training in matching_trainings:
                    copy_same_fields(self, training)
                    training.save()  # копируем поля на случай если изменились
                super().save(*args, **kwargs)
            elif matching_trainings:
                matching_trainings.update(active=False)
                super().save(*args, **kwargs)
            self.create_upcoming_trainings()
        else:
            super().save(*args, **kwargs)
            self.create_upcoming_trainings()

    def delete(self, *args, **kwargs):
        matching_trainings = Training.objects.filter(
                date__gte=datetime.date.today(),
                skill_level=self.skill_level,
                court=self.court,
                day_of_week=self.day_of_week,
            )
        if matching_trainings:
            matching_trainings.delete()
            super().delete(*args, **kwargs)
        else:
            super().delete(*args, **kwargs)

    def create_upcoming_trainings(self, from_monday=False):
        if self.active is True:
            create_trainings_based_on_timeteble_for_x_days(self, Training, 15,
                                                           from_monday)


class Training(TimetableSample):

    MAX_LEARNERS_PER_TRAINING = 16
    TRAINING_DURATION = datetime.timedelta(hours=2)

    class ListOfStatuses(models.IntegerChoices):
        OK = 1, 'OK'
        COACH_REPLACEMENT = 2, 'замена тренера'
        TIME_CHANGE = 3, 'перенос по времени'
        CANCELED = 4, 'отменена'

    status = models.SmallIntegerField(
        verbose_name='статус',
        choices=ListOfStatuses.choices,
        default=ListOfStatuses.OK
    )
    learners = models.ManyToManyField(
        User,
        verbose_name='Посетители',
        blank=True,
        related_name='trainings',
    )
    date = models.DateField('Дата')

    class Meta:
        verbose_name = 'Тренировка'
        verbose_name_plural = 'Тренировки'
        constraints = [
            models.UniqueConstraint(
                fields=['skill_level', 'court', 'date'],
                name='unique_training',
            ),
        ]

    def __str__(self):
        return (
            '{} | {} {} {}'.format(
                self.date,
                self.get_skill_level_display().title(),
                self.court,
                self.get_day_of_week_display(),
            )
        )

    def clean(self):
        if self.day_of_week != self.date.isoweekday():
            raise ValidationError({
                'day_of_week': ValidationError(
                    ('Дата и день недели не соответствуют'), code='invalid'
                ),
                'date': ValidationError(
                    ('Дата и день недели не соответствуют'), code='invalid'
                ),
            })

    def get_free_places(self):
        free_places = self.MAX_LEARNERS_PER_TRAINING - self.learners.count()
        return free_places

    @classmethod
    def get_upcoming_training_or_404(cls, pk):
        return get_upcoming_training_or_404(cls, pk)

    def get_end_datetime(self):
        start_datetime = datetime.datetime(
            year=self.date.year,
            month=self.date.month,
            day=self.date.day,
            hour=self.start_time.hour,
            minute=self.start_time.minute,
        )
        end_datetime = start_datetime + self.TRAINING_DURATION
        return end_datetime

    def is_more_than_an_hour_before_start(self):
        start_time = self.get_end_datetime() - self.TRAINING_DURATION
        an_hour_before_start = start_time - datetime.timedelta(hours=1)
        if datetime.datetime.now() < an_hour_before_start:
            return True
        return False
