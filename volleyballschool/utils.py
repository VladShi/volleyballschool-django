import datetime
from django.core.exceptions import ValidationError


def create_trainings_based_on_timeteble_for_x_days(donor, cls_acceptor, days):
    """Create trainings with certain date based on day of the week from
    timeteble for next x days from current date.

    Args:
        donor (django.db.models.Model): the model instance which provide values
        cls_acceptor (django.db.models.Model):
            the model which instance accept values.
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
