from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (Article, Coach, Court, News, OneTimeTraining,
                     Subscription, SubscriptionSample, Timetable, Training,
                     User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': (
            'first_name', 'patronymic', 'last_name', 'passport_number',
            'passport_data', 'email')
        }),
        ('Баланс', {'fields': ('balance',)}),
        ('Права доступа', {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups',
            'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):

    list_display = ('__str__', 'date',)


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["active"].initial = True
        return form


@admin.register(OneTimeTraining)
class OneTimeTrainingAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super().has_add_permission(request)


@admin.register(SubscriptionSample)
class SubscriptionSampleAdmin(admin.ModelAdmin):

    list_display = ('name', 'amount', 'trainings_qty', 'active',)
    list_filter = ('active',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["name"].help_text = 'например, Абонемент на 4 занятия'
        form.base_fields["validity"].help_text = (
            'отсчитывается со дня посещения первой тренировки'
        )
        form.base_fields["active"].initial = True
        return form


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = ('user', 'purchase_date', 'trainings_qty')


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):

    list_display = ('name', 'active',)
    list_filter = ('active',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["name"].help_text = (
            'например, Зал на ст.м.Октябрьская'
        )
        form.base_fields["active"].initial = True
        return form


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):

    list_display = ('title', 'active',)
    prepopulated_fields = {"slug": ("title",)}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["title"].help_text = (
            'максимум 180 символов'
        )
        form.base_fields["short_description"].help_text = (
            'текст будет отображен в списке статей, максимум 400 символов'
        )
        form.base_fields["active"].initial = True
        return form


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):

    list_display = (
        'court', 'skill_level', 'day_of_week', 'coach', 'start_time',
    )
    list_display_links = list_display
    list_filter = ('court', 'skill_level', 'day_of_week', 'coach')
    ordering = ['court', 'skill_level']
    radio_fields = {'skill_level': admin.VERTICAL}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["active"].initial = True
        return form

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'court', 'skill_level', 'day_of_week', 'start_time',
    )
    list_display_links = list_display
    list_filter = ('court', 'skill_level', 'day_of_week', 'coach')
    ordering = ['-date', 'court', 'skill_level']
    radio_fields = {'status': admin.VERTICAL}
