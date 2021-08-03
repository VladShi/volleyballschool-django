import datetime
from unittest import mock

from django.http.response import Http404
from django.test import TestCase

from .models import (Court, OneTimeTraining, Subscription, Timetable, Training,
                     User)
from .utils import (_date_of_the_current_week_monday,
                    cancel_registration_for_training, copy_same_fields,
                    create_trainings_based_on_timeteble_for_x_days,
                    get_start_date_and_end_date, transform_for_timetable)


class UserModelGetFirstActiveSubscriptionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.user = User.objects.create_user('test_user')
        cls.today = datetime.date.today()
        cls.court1 = Court.objects.create(passport_required=False, active=True)
        cls.past_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=(cls.today-datetime.timedelta(days=1)),
            court=cls.court1,
        )
        cls.future_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=(cls.today+datetime.timedelta(days=1)),
            court=cls.court1,
        )

    def test_no_subsriptions(self):
        self.assertIs(
            self.user.get_first_active_subscription(training_date=self.today),
            None
        )

    def test_not_active_subsriptions(self):
        Subscription.objects.create(
            active=False, user=self.user, trainings_qty=2, validity=30)
        self.assertIs(
            self.user.get_first_active_subscription(training_date=self.today),
            None
        )

    def test_one_active_subscription(self):
        active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        active_sub.purchase_date = self.today
        active_sub.save(update_fields=['purchase_date'])
        self.assertEqual(
            self.user.get_first_active_subscription(
                training_date=self.today,
            ),
            active_sub
        )

    def test_one_active_subscription_with_null_remaining_trainings(self):
        active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        active_sub.purchase_date = self.today
        active_sub.save(update_fields=['purchase_date'])
        active_sub.trainings.add(self.past_training, self.future_training)
        self.assertIs(
            self.user.get_first_active_subscription(
                training_date=self.today,
            ),
            None
        )

    def test_active_and_not_active_subscriptions(self):
        Subscription.objects.create(
            active=False, user=self.user, trainings_qty=2, validity=30)
        active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        active_sub.purchase_date = self.today
        active_sub.save(update_fields=['purchase_date'])
        self.assertEqual(
            self.user.get_first_active_subscription(
                training_date=self.today,
            ),
            active_sub
        )

    def test_two_active_subscriptions(self):
        first_active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        second_active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        first_active_sub.purchase_date = self.today-datetime.timedelta(days=25)
        second_active_sub.purchase_date = self.today
        Subscription.objects.bulk_update(
            [first_active_sub, second_active_sub], ['purchase_date'])
        self.assertEqual(
            self.user.get_first_active_subscription(
                training_date=self.today,
            ),
            first_active_sub
        )

    def test_two_active_subscriptions_one_with_null_remaining_trainings(self):
        first_active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        second_active_sub = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        first_active_sub.purchase_date = self.today-datetime.timedelta(days=25)
        second_active_sub.purchase_date = self.today
        Subscription.objects.bulk_update(
            [first_active_sub, second_active_sub], ['purchase_date'])
        first_active_sub.trainings.add(
            self.past_training, self.future_training)
        self.assertEqual(
            self.user.get_first_active_subscription(
                training_date=self.today,
            ),
            second_active_sub
        )


class SubscriptionModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.user = User.objects.create_user('test_user')
        cls.today = datetime.date.today()
        cls.court1 = Court.objects.create(passport_required=False, active=True)
        cls.past_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=(cls.today-datetime.timedelta(days=1)),
            court=cls.court1,
        )
        cls.future_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=(cls.today+datetime.timedelta(days=1)),
            court=cls.court1,
        )

    def setUp(self):
        self.sub = Subscription.objects.create(
            user=self.user, trainings_qty=2, validity=30)

    def test_get_remaining_trainings_qty_no_trainings(self):
        self.assertEqual(self.sub.get_remaining_trainings_qty(), 2)

    def test_get_remaining_trainings_qty_with_training(self):
        self.sub.trainings.add(self.past_training)
        self.assertEqual(self.sub.get_remaining_trainings_qty(), 1)

    def test_get_remaining_trainings_qty_full_trainings(self):
        self.sub.trainings.add(self.past_training, self.future_training)
        self.assertEqual(self.sub.get_remaining_trainings_qty(), 0)

    def test_get_start_date_if_exist_and_have_training(self):
        self.sub.start_date = self.today
        self.sub.save(update_fields=['start_date'])
        self.assertEqual(self.sub.get_start_date(), self.today)
        self.sub.trainings.add(self.past_training)
        self.assertEqual(self.sub.get_start_date(), self.today)

    def test_get_start_date_if_not_exist_and_have_no_trainings(self):
        yesterday = self.today - datetime.timedelta(days=1)
        self.sub.purchase_date = yesterday
        self.sub.save(update_fields=['purchase_date'])
        self.assertEqual(self.sub.get_start_date(), yesterday)

    def test_get_start_date_not_exist_no_trainings_and_passed_10_days_since_purchase_date(self):
        eleven_days_ago = self.today - datetime.timedelta(days=11)
        self.sub.purchase_date = eleven_days_ago
        self.sub.save(update_fields=['purchase_date'])
        self.assertIs(self.sub.start_date, None)
        self.assertEqual(self.sub.get_start_date(), eleven_days_ago)
        self.assertEqual(self.sub.start_date, eleven_days_ago)

    def test_get_start_date_not_exist_have_training_with_date_later_than_10_days_since_purchase_date(self):
        yesterday = self.today - datetime.timedelta(days=1)
        training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=(self.today+datetime.timedelta(days=10)),
            court=self.court1,
        )
        self.sub.purchase_date = yesterday
        self.sub.save(update_fields=['purchase_date'])
        self.sub.trainings.add(training)
        self.assertEqual(self.sub.get_start_date(), yesterday)
        self.assertIs(self.sub.start_date, None)

    def test_get_start_date_not_exist_have_upcoming_trainings_with_date_earlier_than_10_days_since_purchase_date(self):
        future_training_2 = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=self.today+datetime.timedelta(days=5),
            court=self.court1,
        )
        self.sub.trainings_qty = 3
        self.sub.purchase_date = self.today - datetime.timedelta(days=1)
        self.sub.save(update_fields=['purchase_date'])
        self.sub.trainings.add(future_training_2)
        self.assertEqual(self.sub.get_start_date(), future_training_2.date)
        self.assertIs(self.sub.start_date, None)
        self.sub.trainings.add(self.future_training)
        self.assertEqual(self.sub.get_start_date(), self.future_training.date)
        self.assertIs(self.sub.start_date, None)

    def test_get_start_date_not_exist_have_passed_training_with_date_earlier_than_10_days_since_purchase_date(self):
        self.sub.purchase_date = self.today - datetime.timedelta(days=5)
        self.sub.save(update_fields=['purchase_date'])
        self.sub.trainings.add(self.past_training)
        validity = datetime.timedelta(days=self.sub.validity)
        self.assertEqual(self.sub.get_start_date(), self.past_training.date)
        self.assertEqual(self.sub.start_date, self.past_training.date)
        self.assertEqual(self.sub.end_date, self.past_training.date + validity)

    def test_get_start_date_current_date_later_than_10_days_since_purchase_date(self):
        eleven_days_ago = self.today - datetime.timedelta(days=11)
        self.sub.purchase_date = eleven_days_ago
        self.sub.save(update_fields=['purchase_date'])
        validity = datetime.timedelta(days=self.sub.validity)
        self.assertEqual(self.sub.get_start_date(), eleven_days_ago)
        self.assertEqual(self.sub.start_date, eleven_days_ago)
        self.assertEqual(self.sub.end_date, eleven_days_ago + validity)

    def test_get_end_date_if_exist_and_have_training(self):
        tomorrow = self.today + datetime.timedelta(days=1)
        self.sub.end_date = tomorrow
        self.sub.save(update_fields=['end_date'])
        self.assertEqual(self.sub.get_end_date(), tomorrow)
        self.sub.trainings.add(self.past_training)
        self.assertEqual(self.sub.get_end_date(), tomorrow)

    def test_get_end_date_if_exist_start_date(self):
        eleven_days_ago = self.today - datetime.timedelta(days=11)
        self.sub.start_date = eleven_days_ago
        self.sub.save(update_fields=['start_date'])
        validity = datetime.timedelta(self.sub.validity)
        self.assertIs(self.sub.end_date, None)
        self.assertEqual(self.sub.get_end_date(), eleven_days_ago + validity)
        self.assertEqual(self.sub.end_date, eleven_days_ago + validity)

    def test_get_end_date_if_not_exist_start_date(self):
        five_days_ago = self.today - datetime.timedelta(days=5)
        self.sub.purchase_date = five_days_ago
        self.sub.save(update_fields=['purchase_date'])
        validity = datetime.timedelta(self.sub.validity)
        self.assertEqual(self.sub.get_end_date(), five_days_ago + validity)
        self.assertEqual(self.sub.end_date, None)

    def test_get_end_date_more_than_30_days_since_purchase_but_have_training_in_10_days_adter_purchase(self):
        days_passed_25 = self.today - datetime.timedelta(days=25)
        days_passed_31 = self.today - datetime.timedelta(days=31)
        past_training_2 = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=days_passed_25,
            court=self.court1,
        )
        self.sub.purchase_date = days_passed_31
        self.sub.save(update_fields=['purchase_date'])
        self.sub.trainings.add(past_training_2)
        validity = datetime.timedelta(self.sub.validity)
        self.assertEqual(self.sub.get_end_date(), days_passed_25+validity)
        self.assertEqual(self.sub.start_date, days_passed_25)
        self.assertEqual(self.sub.end_date, days_passed_25+validity)

    def test_is_active_more_than_30_days_since_purchase_but_have_training_in_10_days_adter_purchase(self):
        days_passed_25 = self.today - datetime.timedelta(days=25)
        days_passed_31 = self.today - datetime.timedelta(days=31)
        past_training_2 = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=days_passed_25,
            court=self.court1,
        )
        self.sub.purchase_date = days_passed_31
        self.sub.save(update_fields=['purchase_date'])
        self.sub.trainings.add(past_training_2)
        validity = datetime.timedelta(self.sub.validity)
        self.assertIs(self.sub.is_active(), True)
        self.assertEqual(self.sub.start_date, days_passed_25)
        self.assertEqual(self.sub.end_date, days_passed_25+validity)

    def test_is_active_if_not_active_and_return_qty(self):
        self.sub = Subscription.objects.first()
        self.sub.active = False
        self.sub.save()
        self.assertIs(self.sub.is_active(), False)
        self.assertIs(self.sub.active, False)
        self.assertEqual(self.sub.is_active(return_qty=True), (False, 2))

    def test_is_active_today_is_later_than_the_end_date(self):
        self.sub.end_date = self.today - datetime.timedelta(days=1)
        self.assertIs(self.sub.is_active(), False)
        self.assertIs(self.sub.active, False)
        self.sub.active = True
        self.sub.start_date = None
        self.sub.end_date = self.today-datetime.timedelta(days=1)
        self.sub.save(update_fields=['active', 'start_date', 'end_date'])
        self.assertEqual(self.sub.is_active(return_qty=True), (False, 2))
        self.assertIs(self.sub.active, False)

    def test_is_active_trainings_count_equal_to_trainings_qty_and_possibility_of_canceling_last_training_over(self):
        second_before_now = (
            datetime.datetime.now() - datetime.timedelta(seconds=1))
        start_datetime = second_before_now + datetime.timedelta(hours=1)
        date = datetime.date(
            year=start_datetime.year,
            month=start_datetime.month,
            day=start_datetime.day,
        )
        today_ended_training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            start_time=datetime.time(
                start_datetime.hour,
                start_datetime.minute,
                start_datetime.second,
            ),
            date=date,
            court=self.court1,
        )
        self.sub.trainings.add(self.past_training, today_ended_training)
        self.assertIs(self.sub.is_active(), False)
        self.assertIs(self.sub.active, False)
        self.sub.active = True
        self.sub.start_date, self.sub.end_date = None, None
        self.sub.save(update_fields=['active', 'start_date', 'end_date'])
        self.assertEqual(self.sub.is_active(return_qty=True), (False, 0))
        self.assertIs(self.sub.active, False)

    def test_is_active_trainings_count_equal_to_trainings_qty_and_possibility_of_canceling_last_training_not_over(self):
        second_after_now = (
            datetime.datetime.now() + datetime.timedelta(seconds=1))
        start_datetime = second_after_now + datetime.timedelta(hours=1)
        date = datetime.date(
            year=start_datetime.year,
            month=start_datetime.month,
            day=start_datetime.day,
        )
        today_ended_training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            start_time=datetime.time(
                start_datetime.hour,
                start_datetime.minute,
                start_datetime.second,
            ),
            date=date,
            court=self.court1,
        )
        self.sub.trainings.add(self.past_training, today_ended_training)
        self.assertIs(self.sub.is_active(), True)
        self.sub.active = True
        self.sub.start_date, self.sub.end_date = None, None
        self.sub.save(update_fields=['active', 'start_date', 'end_date'])
        self.assertEqual(self.sub.is_active(return_qty=True), (True, 0))
        self.assertIs(self.sub.active, True)

    def test_is_active_today_is_earlier_than_end_date_and_trainings_count_not_equal_to_trainings_qty(self):
        self.sub.end_date = self.today + datetime.timedelta(days=1)
        self.sub.save(update_fields=['end_date'])
        self.assertIs(self.sub.is_active(), True)
        self.assertIs(self.sub.active, True)
        self.sub.trainings.add(self.past_training)
        self.assertIs(self.sub.is_active(), True)
        self.assertIs(self.sub.active, True)
        self.assertEqual(self.sub.is_active(return_qty=True), (True, 1))
        self.assertIs(self.sub.active, True)
        self.sub.trainings.remove(self.past_training)
        self.assertEqual(self.sub.is_active(return_qty=True), (True, 2))
        self.assertIs(self.sub.active, True)


class OneTimeTrainingTestCase(TestCase):
    def test_save_inability_to_save_more_than_one_record(self):
        record1 = OneTimeTraining.objects.create(price=1)
        record2 = OneTimeTraining.objects.create(price=2)
        self.assertEqual(OneTimeTraining.objects.first(), record1)
        self.assertNotEqual(OneTimeTraining.objects.last(), record2)
        self.assertNotEqual(OneTimeTraining.objects.first(), record2)
        self.assertEqual(OneTimeTraining.objects.all().count(), 1)


class TrainingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.today = datetime.date.today()
        cls.court1 = Court.objects.create(passport_required=False, active=True)
        cls.upcoming_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            date=cls.today+datetime.timedelta(days=2),
            start_time=datetime.time(18, 00, 00),
            court=cls.court1,
        )

    def test_get_end_datetime(self):
        training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            date=datetime.datetime(2021, 7, 31),
            start_time=datetime.time(23, 59, 00),
            court=self.court1,
        )
        end_time = (
            datetime.datetime(
                1970, 1, 1,
                hour=training.start_time.hour,
                minute=training.start_time.minute,
                second=training.start_time.second,
            )
            + training.TRAINING_DURATION
        )
        end_datetime = datetime.datetime(
            year=2021,
            month=8,
            day=1,
            hour=end_time.hour,
            minute=end_time.minute,
            second=end_time.second,
        )
        self.assertEqual(training.get_end_datetime(), end_datetime)

    def test_get_free_places(self):
        Training.MAX_LEARNERS_PER_TRAINING = 2
        user1 = User.objects.create_user('test_user1')
        user2 = User.objects.create_user('test_user2')
        training = self.upcoming_training
        training.learners.add(user1, user2)
        self.assertEqual(training.get_free_places(), 0)
        training.learners.remove(user1)
        self.assertEqual(training.get_free_places(), 1)
        training.learners.remove(user2)
        self.assertEqual(training.get_free_places(), 2)

    def test_is_more_than_an_hour_before_start_is_true(self):
        after_now_61_minutes = (
            datetime.datetime.now() + datetime.timedelta(hours=1, minutes=1))
        training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            date=datetime.date(
                after_now_61_minutes.year,
                after_now_61_minutes.month,
                after_now_61_minutes.day,
            ),
            start_time=datetime.time(
                after_now_61_minutes.hour,
                after_now_61_minutes.minute,
                after_now_61_minutes.second,
            ),
            court=self.court1,
        )
        self.assertIs(training.is_more_than_an_hour_before_start(), True)

    def test_is_more_than_an_hour_before_start_is_false(self):
        after_now_59_minutes = (datetime.datetime.now()
                                + datetime.timedelta(minutes=59))
        training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            date=datetime.date(
                after_now_59_minutes.year,
                after_now_59_minutes.month,
                after_now_59_minutes.day,
            ),
            start_time=datetime.time(
                after_now_59_minutes.hour,
                after_now_59_minutes.minute,
                after_now_59_minutes.second,
            ),
            court=self.court1,
        )
        training.save(update_fields=(['date', 'start_time']))
        self.assertIs(training.is_more_than_an_hour_before_start(), False)

    def test_get_upcoming_training_or_404_for_upcoming_training(self):
        pk = self.upcoming_training.pk
        self.assertEqual(
            Training.get_upcoming_training_or_404(pk=pk),
            self.upcoming_training
        )

    def test_get_upcoming_training_or_404_for_past_training(self):
        past_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            date=self.today-datetime.timedelta(days=1),
            court=self.court1,
        )
        pk = past_training.pk
        with self.assertRaises(Http404):
            Training.get_upcoming_training_or_404(pk=pk)


class UtilsTestCase(TestCase):
    def test_copy_same_fields(self):
        court1 = Court.objects.create(passport_required=False, active=True)
        court2 = Court.objects.create(passport_required=False, active=True)
        timetable = Timetable.objects.create(
            day_of_week=1,
            skill_level=1,
            court=court1,
            start_time=datetime.time(18, 00, 00),
            active=True,
        )
        Training.objects.all().delete()
        training = Training.objects.create(
            day_of_week=2,
            skill_level=2,
            date=datetime.datetime(2021, 7, 31),
            start_time=datetime.time(20, 30, 00),
            court=court2,
            active=False,
        )
        copy_same_fields(timetable, training)
        training.save()
        self.assertEqual(training.day_of_week, 1)
        self.assertEqual(training.skill_level, 1)
        self.assertEqual(training.court, court1)
        self.assertEqual(training.start_time, datetime.time(18, 00, 00))
        self.assertEqual(training.active, True)

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_date_of_the_current_week_monday(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2010, 1, 1)
        date = _date_of_the_current_week_monday()
        self.assertEqual(date, datetime.date(2009, 12, 28))

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_get_start_date_and_end_date(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 1, 1)
        start_date, end_date = get_start_date_and_end_date(2)
        self.assertEqual(start_date, datetime.date(2019, 12, 30))
        self.assertEqual(end_date, datetime.date(2020, 1, 12))

    def test_transform_for_timetable(self):
        court1 = Court.objects.create(
            name='Корт1', passport_required=False, active=True)
        court2 = Court.objects.create(
            name='Корт2', passport_required=False, active=True)
        for i, j in ((2, 19), (4, 22), (2, 26), (4, 29), (7, 31)):
            c = court1
            if j % 2 != 0:
                c = court2
            Training.objects.create(
                day_of_week=i,
                skill_level=1,
                start_time=datetime.time(18, 00, 00),
                date=datetime.date(2020, 5, j),
                court=c,
            )
        query_set = Training.objects.all()
        start_date = datetime.date(2020, 5, 18)
        expected_result = [
            {'name': court1,
             'weeks': [
                 [{'date': datetime.date(2020, 5, 18)},  # пн.
                  {'date': datetime.date(2020, 5, 19)},  # вт.
                  {'date': datetime.date(2020, 5, 20)},  # ср.
                  {'date': datetime.date(2020, 5, 21)},  # чт.
                  Training.objects.get(date=datetime.date(2020, 5, 22)),  # пт.
                  {'date': datetime.date(2020, 5, 23)},  # сб.
                  {'date': datetime.date(2020, 5, 24)},  # вс.
                  ],
                 [{'date': datetime.date(2020, 5, 25)},  # пн.
                  Training.objects.get(date=datetime.date(2020, 5, 26)),  # вт.
                  {'date': datetime.date(2020, 5, 27)},  # ср.
                  {'date': datetime.date(2020, 5, 28)},  # чт.
                  {'date': datetime.date(2020, 5, 29)},  # пт.
                  {'date': datetime.date(2020, 5, 30)},  # сб.
                  {'date': datetime.date(2020, 5, 31)},  # вс.
                  ],
             ]
             },
            {'name': court2,
             'weeks': [
                 [{'date': datetime.date(2020, 5, 18)},
                  Training.objects.get(date=datetime.date(2020, 5, 19)),
                  {'date': datetime.date(2020, 5, 20)},
                  {'date': datetime.date(2020, 5, 21)},
                  {'date': datetime.date(2020, 5, 22)},
                  {'date': datetime.date(2020, 5, 23)},
                  {'date': datetime.date(2020, 5, 24)},
                  ],
                 [{'date': datetime.date(2020, 5, 25)},
                  {'date': datetime.date(2020, 5, 26)},
                  {'date': datetime.date(2020, 5, 27)},
                  {'date': datetime.date(2020, 5, 28)},
                  Training.objects.get(date=datetime.date(2020, 5, 29)),
                  {'date': datetime.date(2020, 5, 30)},
                  Training.objects.get(date=datetime.date(2020, 5, 31)),
                  ],
             ]
             }
        ]
        self.assertEqual(transform_for_timetable(query_set, start_date, 2),
                         expected_result)

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_create_trainings_based_on_timeteble_for_x_days(self, 
                                                            mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        court1 = Court.objects.create(passport_required=False, active=True)
        timetable = Timetable.objects.create(
                day_of_week=2,
                skill_level=1,
                start_time=datetime.time(18, 00, 00),
                court=court1,
        )
        Training.objects.all().delete()
        create_trainings_based_on_timeteble_for_x_days(timetable, Training, 15)
        all_trainings = Training.objects.order_by('date').all()
        self.assertEqual(all_trainings[0].date,
                         datetime.date(2020, 10, 13))
        self.assertEqual(all_trainings[1].date,
                         datetime.date(2020, 10, 20))
        self.assertEqual(all_trainings.count(), 2)

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_create_trainings_based_on_timeteble_for_x_days_from_monday_true(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        court1 = Court.objects.create(passport_required=False, active=True)
        timetable = Timetable.objects.create(
            day_of_week=2,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            court=court1,
        )
        Training.objects.all().delete()
        create_trainings_based_on_timeteble_for_x_days(
            timetable, Training, days=21, from_monday=True)
        all_trainings = Training.objects.order_by('date').all()
        self.assertEqual(all_trainings[0].date,
                         datetime.date(2020, 10, 6))
        self.assertEqual(all_trainings[1].date,
                         datetime.date(2020, 10, 13))
        self.assertEqual(all_trainings[2].date,
                         datetime.date(2020, 10, 20))
        self.assertEqual(all_trainings.count(), 3)

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_create_trainings_based_on_timeteble_for_x_days_if_training_exist(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        court1 = Court.objects.create(passport_required=False, active=True)
        timetable = Timetable.objects.create(
            day_of_week=2,
            skill_level=1,
            start_time=datetime.time(18, 00, 00),
            court=court1,
        )
        Training.objects.all().delete()
        Training.objects.create(
            day_of_week=2,
            skill_level=1,
            date=datetime.datetime(2020, 10, 13),
            start_time=datetime.time(18, 00, 00),
            court=court1,
        )
        create_trainings_based_on_timeteble_for_x_days(timetable, Training, 15)
        all_trainings = Training.objects.order_by('date').all()
        self.assertEqual(all_trainings[0].date,
                         datetime.date(2020, 10, 13))
        self.assertEqual(all_trainings[1].date,
                         datetime.date(2020, 10, 20))
        self.assertEqual(all_trainings.count(), 2)

    def test_cancel_registration_for_training_more_than_an_hour_before_start(self):
        after_now_61_minutes = (
            datetime.datetime.now() + datetime.timedelta(hours=1, minutes=1))
        user1 = User.objects.create_user('test_user1')
        user2 = User.objects.create_user('test_user2')
        court1 = Court.objects.create(passport_required=False, active=True)
        training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            date=datetime.date(
                after_now_61_minutes.year,
                after_now_61_minutes.month,
                after_now_61_minutes.day,
            ),
            start_time=datetime.time(
                after_now_61_minutes.hour,
                after_now_61_minutes.minute,
                after_now_61_minutes.second,
            ),
            court=court1,
        )
        subscription = Subscription.objects.create(
            user=user1, trainings_qty=2, validity=30)
        training.learners.add(user1, user2)
        subscription.trainings.add(training)
        cancel_registration_for_training(
            user1, training, price_for_one_training=900)
        self.assertEqual(training.learners.count(), 1)
        self.assertEqual(subscription.trainings.count(), 0)
        self.assertIn(user2, training.learners.all())
        cancel_registration_for_training(
            user2, training, price_for_one_training=900)
        self.assertEqual(training.learners.count(), 0)
        self.assertEqual(user2.balance, 900)

    def test_cancel_registration_for_training_less_than_an_hour_before_start(self):
        after_now_59_minutes = (
            datetime.datetime.now() + datetime.timedelta(minutes=59))
        user1 = User.objects.create_user('test_user1')
        court1 = Court.objects.create(passport_required=False, active=True)
        training = Training.objects.create(
            day_of_week=1,
            skill_level=2,
            date=datetime.date(
                after_now_59_minutes.year,
                after_now_59_minutes.month,
                after_now_59_minutes.day,
            ),
            start_time=datetime.time(
                after_now_59_minutes.hour,
                after_now_59_minutes.minute,
                after_now_59_minutes.second,
            ),
            court=court1,
        )
        training.learners.add(user1)
        cancel_registration_for_training(
            user1, training, price_for_one_training=850)
        self.assertEqual(training.learners.count(), 1)
        self.assertIn(user1, training.learners.all())
