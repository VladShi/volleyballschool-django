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


@admin.register(Courts)
class CourtsAdmin(admin.ModelAdmin):

    list_display = ('name', 'active',)
