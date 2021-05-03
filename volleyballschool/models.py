from django.db import models

# Create your models here.

class News(models.Model):
    title = models.CharField('Заголовок', max_length=120)
    text = models.TextField('Текст', blank=True)
    image = models.ImageField('Изображение', upload_to='news_images/', blank=True)
    date = models.DateField('Дата', auto_now_add=True)
    
    def __str__(self):
        return self.title[:30] + '...'
    
    class Meta:
        ordering = ["-date"]
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
