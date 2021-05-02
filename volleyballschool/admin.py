from django.contrib import admin

from .models import News

# Register your models here.
class NewsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date',)

admin.site.register(News, NewsAdmin)