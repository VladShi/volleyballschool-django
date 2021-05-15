from django.core.management.base import BaseCommand
from volleyballschool.models import Timetable


class Command(BaseCommand):
    help = (
        'For volleyballscholl app create trainings with certain date' +
        'based on day of the week from timetebles for next 15 days' +
        'from current date.' +
        '\n Run once a week'
    )

    def handle(self, *args, **options):
        active_timetables = Timetable.objects.filter(active=True)
        for timetable in active_timetables:
            timetable.create_trainings()
