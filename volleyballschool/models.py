from django.db import models


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
