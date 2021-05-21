from django.core.management.base import BaseCommand
from volleyballschool.models import Timetable


class Command(BaseCommand):
    help = (
        'For volleyballscholl app create trainings with certain date ' +
        'based on day of the week from timetebles for next 15 days ' +
        'from current date.\n Run once a week'
    )

    def handle(self, *args, **options):
        active_timetables = Timetable.objects.filter(active=True)
        if not options['from_monday']:
            for timetable in active_timetables:
                timetable.create_upcoming_trainings()
        else:
            for timetable in active_timetables:
                timetable.create_upcoming_trainings(from_monday=True)

    def add_arguments(self, parser):
        parser.add_argument(
            '-fm',
            '--from_monday',
            action='store_true',
            default=False,
            help='Create trainings from Monday of the current week, not from \
                  current day'
        )
