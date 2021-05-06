from django.db import models

from ckeditor_uploader.fields import RichTextUploadingField


class News(models.Model):

    title = models.CharField('Заголовок', max_length=120)
    text = models.TextField('Текст', blank=True)
    image = models.ImageField(
        'Изображение', upload_to='news_images/', blank=True)
    date = models.DateField('Дата', auto_now_add=True)

    def __str__(self):
        return self.title[:30] + '...'

    class Meta:
        ordering = ["-date"]
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'


class Coaches(models.Model):

    name = models.CharField('Имя', max_length=100)
    description = models.TextField('Описание')
    photo = models.ImageField(
        'Фото', upload_to='photos_of_coaches/', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'


class SubscriptionSamples(models.Model):
    """Шаблоны Абонементов"""

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
            return "укажите кол-во тренировок по абонементу"

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'


class OneTimeTraining(models.Model):
    """В таблице должна находиться только единственная запись с ценной за одну
    тренировку. В админке отключаем возможность добавления больше одной записи
    """

    price = models.PositiveSmallIntegerField('Цена(руб.)')

    def __str__(self):
        return 'Изменить стоимость разового занятия'

    class Meta:
        verbose_name = 'Стоимость разового занятия'
        verbose_name_plural = 'Стоимость разового занятия'


class Courts(models.Model):
    """Волейбольные залы"""

    name = models.CharField('Имя', max_length=120)
    description = models.TextField('Описание', blank=True)
    photo = models.ImageField(
        'Фото', upload_to='photos_of_courts/', blank=True)
    address = models.CharField('Адрес', max_length=120)
    metro = models.CharField('Станция метро', max_length=50)
    longitude = models.DecimalField(
        'Долгота', max_digits=9, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(
        'Широта', max_digits=9, decimal_places=6, blank=True, null=True)
    active = models.BooleanField('Активный')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Зал'
        verbose_name_plural = 'Залы'


class Articles(models.Model):

    title = models.CharField('Заголовок', max_length=180)
    slug = models.SlugField('Slug( URL )', max_length=200,
                            unique=True, db_index=True)
    short_description = models.TextField(
        'Краткое описание статьи', max_length=400)
    text = RichTextUploadingField('Текст')
    active = models.BooleanField('Активна')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article-detail', args=[str(self.slug)])

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
