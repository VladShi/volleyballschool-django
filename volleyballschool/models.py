import datetime

from ckeditor_uploader.fields import RichTextUploadingField

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from .utils import (
    create_trainings_based_on_timeteble_for_x_days, copy_same_fields,
)


class User(AbstractUser):
    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    balance = models.DecimalField(
        verbose_name='Баланс',
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

    @property
    def price_for_one_training(self):
        try:
            return int(self.amount / self.trainings_qty)
        except ZeroDivisionError:
            return "укажите кол-во тренировок по данному абонементу"


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

    def create_trainings(self):
        if self.active is True:
            create_trainings_based_on_timeteble_for_x_days(self, Training, 15)

    def save(self, *args, **kwargs):
        if self.id:  # если расписание уже создано ранее
            matching_trainings = Training.objects.filter(
                Q(date__gte=datetime.date.today()),
                Q(skill_level=self.skill_level),
                Q(court=self.court),
                Q(day_of_week=self.day_of_week),
                Q(status=1),
            )
            if self.active is True and matching_trainings:
                for training in matching_trainings:
                    copy_same_fields(self, training)
                    training.save()  # копируем поля на случай если изменились
                super().save(*args, **kwargs)
            elif matching_trainings:
                matching_trainings.update(active=False)
                super().save(*args, **kwargs)
            self.create_trainings()
        else:
            super().save(*args, **kwargs)
            self.create_trainings()

    def delete(self, *args, **kwargs):
        matching_trainings = Training.objects.filter(
                Q(date__gte=datetime.date.today()),
                Q(skill_level=self.skill_level),
                Q(court=self.court),
                Q(day_of_week=self.day_of_week),
            )
        if matching_trainings:
            matching_trainings.delete()
            super().delete(*args, **kwargs)
        else:
            super().delete(*args, **kwargs)


class Training(TimetableSample):

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
        if self.day_of_week != self.date.isoweekday:
            raise ValidationError({
                'day_of_week': ValidationError(
                    ('Дата и день недели не соответствуют'), code='invalid'
                ),
                'date': ValidationError(
                    ('Дата и день недели не соответствуют'), code='invalid'
                ),
            })
