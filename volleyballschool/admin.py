from django.contrib import admin

from .models import News, Coaches, SubscriptionSamples, OneTimeTraining


class NewsAdmin(admin.ModelAdmin):

    list_display = ('__str__', 'date',)


class OneTimeTrainingAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        return super().has_add_permission(request)


class SubscriptionSamplesAdmin(admin.ModelAdmin):

    list_display = ('name', 'amount', 'trainings_qty', 'active',)


admin.site.register(News, NewsAdmin)
admin.site.register(Coaches)
admin.site.register(SubscriptionSamples, SubscriptionSamplesAdmin)
admin.site.register(OneTimeTraining, OneTimeTrainingAdmin)
