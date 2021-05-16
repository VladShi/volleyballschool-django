import datetime
from django.core.exceptions import ValidationError


def create_trainings_based_on_timeteble_for_x_days(donor, cls_acceptor, days):
    """Create trainings with certain date based on day of the week from
    timeteble for next x days from current date.

    Args:
        donor (django.db.models.Model): the model instance which provide values
        cls_acceptor (django.db.models.Model):
            the model which new instance accept values.
        days (int): number of days from today for creating trainings

    Raises:
        e: Validation errors except Unique Constraint violation

    Returns:
        None
    """
    date_list = [
        datetime.date.today() + datetime.timedelta(days=x) for x in range(days)
    ]
    for day in date_list:
        if donor.day_of_week == day.isoweekday():
            acceptor_instance = cls_acceptor()
            copy_same_fields(donor, acceptor_instance)
            acceptor_instance.date = day
            try:
                acceptor_instance.full_clean(validate_unique=True)
            except ValidationError as e:
                if 'с такими значениями' in e.messages[0] \
                        and 'уже существует' in e.messages[0]:
                    return  # f'Тренировка c датой {training.date} '
                    # + f'в {training.court} '
                    # + f'и на {training.get_skill_level_display()}'
                    # + ' уже существует'
                raise e
            acceptor_instance.save()


def copy_same_fields(donor, acceptor):
    """Copy field values from one django model instance to another django
    model instance, if the field names are equal.(Except the 'id' field)

    Args:
        donor (django.db.models.Model): the model instance which provide values
        acceptor (django.db.models.Model):
            the model instance which accept values
    """

    acceptor_field_names = []
    acceptor_fields = acceptor._meta.get_fields()
    for field in acceptor_fields:
        acceptor_field_names.append(field.name)

    donor_fields = donor._meta.get_fields()

    for field in donor_fields:
        if field.name != 'id' and field.name in acceptor_field_names:
            field_value_from_donor = getattr(donor, field.name)
            setattr(acceptor, field.name, field_value_from_donor)


def get_start_date_and_end_date(number_of_weeks):
    """Return the current week Monday date as start_date. And return Sunday
    date of current+[number_of_week] week as end_date.

    Args:
        number_of_weeks ([int]): Number of weeks to display in the timetable

    Returns:
        [datetime.date]: start_date, end_date
    """
    current_week_day = datetime.date.today().isoweekday()
    start_date = (  # Monday of the current week
        datetime.date.today()
        - datetime.timedelta(days=(current_week_day-1))
    )
    end_date = start_date + datetime.timedelta(days=7*number_of_weeks-1)
    return start_date, end_date


def transform_for_timetable(query_set, start_date, number_of_weeks):
    """Group [query_set] by courts. For each court create dictionary with
    name of court and with lists in [number_of_weeks] quantity with seven
    elements. Each element of list is related to day of week. The element
    contains date, accessible by [date] key, and Training model object if
    it exist for that day.

    Args:
        query_set: QuerySet
        start_date ([datetime.date): Monday of the current week
        number_of_weeks ([int]): Number of weeks to display in the timetable

    Returns:
        [dict]:
    {'name': court object, 'weeks': [
    [{'date': datetime.date()},  # monday of current week
     query_set.first(),  # object that matches the date and the court
     ...
     {'date': datetime.date(2001, 10, 2)},  # sunday of current week
     ],
    [...  # seven element, monday to sunday next week
     ],
    ]}
    """
    courts = set()
    for training in query_set:
        courts.add(training.court)
    transformed_query_set = []
    for court in courts:
        trainigs_for_court = dict()
        trainigs_for_court['name'] = court
        trainigs_for_court['weeks'] = [[] for _ in range(number_of_weeks)]
        for week_number in range(number_of_weeks):
            for date in (
                start_date + datetime.timedelta(n) for n
                in range(7*week_number, 7*(week_number+1))
            ):
                # if query_set.filter(date=date, court=court).exists():
                # при использовании строчки выше, каждую итерацию происходит
                # запрос к базе и в итоге выходит 60 запросов к бд и секунда на
                # загрузку страницы. Непонятно почему
                flag = True
                for query in query_set:
                    if query.date == date and query.court == court:
                        trainigs_for_court['weeks'][week_number].append(
                            query
                        )
                        flag = False
                        break
                if flag:
                    trainigs_for_court['weeks'][week_number].append(
                        {'date': date}
                            )
        transformed_query_set.append(trainigs_for_court)
    return transformed_query_set