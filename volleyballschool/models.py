from django.db import models
from django.contrib.auth.models import AbstractUser

from ckeditor_uploader.fields import RichTextUploadingField


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

    def __str__(self):
        return self.title[:30] + '...'

    class Meta:
        ordering = ["-date"]
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'


class Coach(models.Model):

    name = models.CharField('Имя', max_length=100)
    description = models.TextField('Описание')
    photo = models.ImageField(
        verbose_name='Фото',
        upload_to='photos_of_coaches/',
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'


class SubscriptionSample(models.Model):
    """Шаблон Абонемента"""

    name = models.CharField('Наименование', max_length=80)
    amount = models.PositiveIntegerField('Стоимость(руб.)')
    trainings_qty = models.PositiveSmallIntegerField('Количество тренировок')
    validity = models.PositiveSmallIntegerField('Срок действия(дней)')
    active = models.BooleanField('Активный')

    def __str__(self):
        return self.name

    @property
    def price_for_one_training(self):
        try:
            return int(self.amount / self.trainings_qty)
        except ZeroDivisionError:
            return "укажите кол-во тренировок по данному абонементу"

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'


class OneTimeTraining(models.Model):
    """В таблице должна находиться только единственная запись с ценной
    за разовое занятие. В админке отключаем возможность добавления
    больше одной записи в модель.
    """

    price = models.PositiveSmallIntegerField('Цена(руб.)')

    def __str__(self):
        return 'Изменить стоимость разового занятия'

    class Meta:
        verbose_name = 'Стоимость разового занятия'
        verbose_name_plural = 'Стоимость разового занятия'


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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Зал'
        verbose_name_plural = 'Залы'


class Article(models.Model):

    title = models.CharField('Заголовок', max_length=180)
    slug = models.SlugField(
        verbose_name='Slug( URL )',
        max_length=200,
        unique=True,
        db_index=True,
    )
    short_description = models.TextField(
        verbose_name='Краткое описание статьи',
        max_length=400,
    )
    text = RichTextUploadingField('Текст')
    active = models.BooleanField('Активна')

    def __str__(self):
        return self.title[:40] + '...'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article-detail', args=[str(self.slug)])

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'


class Timetable(models.Model):

    class DaysOfTheWeek(models.TextChoices):
        MONDAY = 'Mon', 'Понедельник'
        TUESDAY = 'Tue', 'Вторник'
        WEDNESDAY = 'Wed', 'Среда'
        THURSDAY = 'Thu', 'Четверг'
        FRIDAY = 'Fri', 'Пятница'
        SATURDAY = 'Sat', 'Суббота'
        SUNDAY = 'Sun', 'Воскресенье'

    class SkillLevels(models.IntegerChoices):
        BEGGINER = 1, 'начальный уровень'
        BEGGINER_PLUS = 2, 'уровень начальный+'
        MIDDLE = 3, 'средний уровень'

    day_of_week = models.CharField(
        verbose_name='день недели',
        max_length=3,
        choices=DaysOfTheWeek.choices,
    )
    skill_level = models.IntegerField(
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
        default='Тренер не назначен',
    )
    start_time = models.TimeField('время начала')

    def __str__(self):
        return (
            f'{self.get_skill_level_display().title()}  {self.court} \
              {self.get_day_of_week_display()}'
        )

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
