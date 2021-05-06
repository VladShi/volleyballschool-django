from django.contrib import admin

from .models import News, Coaches, SubscriptionSamples, OneTimeTraining, Courts


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):

    list_display = ('__str__', 'date',)


@admin.register(Coaches)
class CoachesAdmin(admin.ModelAdmin):
    pass


@admin.register(OneTimeTraining)
class OneTimeTrainingAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super().has_add_permission(request)


@admin.register(SubscriptionSamples)
class SubscriptionSamplesAdmin(admin.ModelAdmin):

    list_display = ('name', 'amount', 'trainings_qty', 'active',)
    list_filter = ('active',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["name"].help_text = 'например, Абонемент на 4 занятия'
        form.base_fields["validity"].help_text = (
            'отсчитывается со дня посещения первой тренировки')
        form.base_fields["active"].initial = True
        return form


@admin.register(Courts)
class CourtsAdmin(admin.ModelAdmin):

    list_display = ('name', 'active',)
    list_filter = ('active',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["name"].help_text = (
            'например, Зал на ст.м.Октябрьская')
        form.base_fields["active"].initial = True
        return form
