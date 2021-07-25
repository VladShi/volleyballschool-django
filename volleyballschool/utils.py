import datetime
from django.core.exceptions import ValidationError
from django.http import Http404


def create_trainings_based_on_timeteble_for_x_days(
    timetable,
    training_class,
    days,
    from_monday=False,
):
    """Create trainings with certain date based on day of the week from
    timeteble for next x days from current date.

    Args:
        timetable (django.db.models.Model): the model instance which provide
        values except certain date
        training_class (django.db.models.Model):
            the model which new instance accept values from timetable and gets
            certain date.
        days (int): number of days from today for creating trainings

    Raises:
        e: Validation errors except Unique Constraint violation

    Returns:
        None
    """
    if from_monday:
        date_list = [
            _date_of_the_current_week_monday()
            + datetime.timedelta(days=x) for x in range(days)
        ]
    elif not from_monday:
        date_list = [
            datetime.date.today()
            + datetime.timedelta(days=x) for x in range(days)
        ]
    for day in date_list:
        if timetable.day_of_week == day.isoweekday():
            training_instance = training_class()
            copy_same_fields(timetable, training_instance)
            training_instance.date = day
            try:
                training_instance.full_clean(validate_unique=True)
            except ValidationError as e:
                if 'с такими значениями' in e.messages[0] \
                        and 'уже существует' in e.messages[0]:
                    continue  # f'Тренировка c датой {training.date} '
                    # + f'в {training.court} '
                    # + f'и на {training.get_skill_level_display()}'
                    # + ' уже существует'
                raise e
            training_instance.save()


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
    date of current+[number_of_weeks] week as end_date.

    Args:
        number_of_weeks ([int]): Number of weeks to display in the timetable

    Returns:
        [datetime.date]: start_date, end_date
    """
    start_date = _date_of_the_current_week_monday()
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
                for query in query_set:
                    if query.date == date and query.court == court:
                        trainigs_for_court['weeks'][week_number].append(
                            query
                        )
                        break
                else:
                    trainigs_for_court['weeks'][week_number].append(
                        {'date': date}
                    )
        transformed_query_set.append(trainigs_for_court)
    return transformed_query_set


def get_upcoming_training_or_404(model, pk):
    """Return a training object by pk if training has not finished, else raise
    Http404.
    Including select_related for field 'court' and prefetch_related for field
    'learners'.

    Raises:
        Http404

    Returns:
        [object]: the model object
    """
    try:
        training = model.objects.select_related(
            'court'
        ).prefetch_related(
            'learners'
        ).filter(
            date__gte=datetime.date.today()
        ).get(pk=pk)
    except model.DoesNotExist:
        raise Http404()
    if datetime.datetime.now() > training.get_end_datetime():
        raise Http404()
    return training


def _date_of_the_current_week_monday():
    current_week_day = datetime.date.today().isoweekday()
    monday_of_the_current_week = (
        datetime.date.today()
        - datetime.timedelta(days=(current_week_day-1))
    )
    return monday_of_the_current_week


def cancel_registration_for_training(user, training, price_for_one_training):
    if (
        user in training.learners.all()
        and training.is_more_than_an_hour_before_start()
    ):
        subscription_of_user = (
            training.subscription_set.filter(user=user).first()
        )
        if subscription_of_user:
            subscription_of_user.trainings.remove(training)
        else:
            user.balance += price_for_one_training
            user.save(update_fields=['balance'])
        training.learners.remove(user)
