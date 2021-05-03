from django.contrib import admin

from .models import News, Coaches

# Register your models here.


class NewsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'date',)


admin.site.register(News, NewsAdmin)
admin.site.register(Coaches)
