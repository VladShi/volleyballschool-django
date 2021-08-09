import datetime
from unittest import mock

from django.http.response import Http404
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from .models import (Article, Coach, Court, News, OneTimeTraining,
                     Subscription, SubscriptionSample, Timetable, Training,
                     User)
from .utils import (_date_of_the_current_week_monday,
                    cancel_registration_for_training, copy_same_fields,
                    create_trainings_based_on_timeteble_for_x_days,
                    get_start_date_and_end_date, transform_for_timetable)


class UserModelGetFirstActiveSubscriptionTests(TestCase):
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


class SubscriptionModelTests(TestCase):
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
            datetime.datetime.now() - datetime.timedelta(seconds=3))
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
            datetime.datetime.now() + datetime.timedelta(seconds=3))
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


class OneTimeTrainingTests(TestCase):
    def test_save_inability_to_save_more_than_one_record(self):
        record1 = OneTimeTraining.objects.create(price=1)
        record2 = OneTimeTraining.objects.create(price=2)
        self.assertEqual(OneTimeTraining.objects.first(), record1)
        self.assertNotEqual(OneTimeTraining.objects.last(), record2)
        self.assertNotEqual(OneTimeTraining.objects.first(), record2)
        self.assertEqual(OneTimeTraining.objects.all().count(), 1)


class TrainingTests(TestCase):
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


class UtilsTests(TestCase):
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
        for i, j in ((5, 15), (2, 19), (4, 22), (2, 26), (4, 29), (7, 31)):
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


class TimetableTests(TestCase):
    def setUp(self,):
        # for the test use today date as datetime.date(2020, 10, 10)
        self.court1 = Court.objects.create(passport_required=False, active=True)
        self.timetable = Timetable.objects.create(
            day_of_week=6,
            skill_level=1,
            court=self.court1,
            start_time=datetime.time(18, 00, 00),
            active=True,
        )
        Training.objects.all().delete()
        self.training_past, self.training_1, self.training_2 = [
            Training.objects.create(
                day_of_week=6,
                skill_level=1,
                start_time=datetime.time(18, 00, 00),
                date=datetime.date(2020, 10, day),
                court=self.court1,
            )
            for day in (3, 10, 17)
        ]
        self.not_matching_training = Training.objects.create(
                day_of_week=4,
                skill_level=2,
                start_time=datetime.time(17, 00, 00),
                date=datetime.date(2020, 10, 15),
                court=self.court1,
            )

    @mock.patch('volleyballschool.models.datetime', wraps=datetime)
    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_save_if_has_matching_trainings(self, mocked_datetime, mock_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        mock_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        self.timetable.start_time = datetime.time(20, 00, 00)
        self.timetable.skill_level = 3
        self.timetable.save()
        all_trainings = Training.objects.all()
        training_past = all_trainings.get(pk=self.training_past.pk)
        training_1 = all_trainings.get(pk=self.training_1.pk)
        training_2 = all_trainings.filter(pk=self.training_2.pk).first()
        not_matching_training = all_trainings.get(
            pk=self.not_matching_training.pk)
        self.assertEqual(training_past.skill_level, 1)
        self.assertEqual(training_past.start_time, datetime.time(18, 00, 00))
        self.assertEqual(training_1.start_time, datetime.time(20, 00, 00))
        self.assertEqual(training_1.skill_level, 3)
        self.assertEqual(not_matching_training.start_time,
                         datetime.time(17, 00, 00))
        self.assertEqual(not_matching_training.skill_level, 2)
        if training_2:
            self.assertEqual(training_2.start_time, datetime.time(20, 00, 00))
            self.assertEqual(training_2.skill_level, 3)

    @mock.patch('volleyballschool.models.datetime', wraps=datetime)
    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_save_timetable_has_no_matching_trainings(self, mocked_datetime, mock_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        mock_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        Training.objects.filter(
            day_of_week=6,
            skill_level=1,
            court=self.court1,
        ).all().delete()
        self.timetable.save()
        self.assertIsNotNone(Training.objects.filter(
            skill_level=1, day_of_week=6, court=self.court1).first())
        self.assertEqual(
            Training.objects.get(pk=self.not_matching_training.pk).skill_level,
            2
        )

    @mock.patch('volleyballschool.models.datetime', wraps=datetime)
    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_save_timetable_has_no_matching_trainings_and_changed(self, mocked_datetime, mock_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        mock_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        Training.objects.filter(
            day_of_week=6,
            skill_level=1,
            court=self.court1,
        ).all().delete()
        self.timetable.start_time = datetime.time(20, 00, 00)
        self.timetable.skill_level = 3
        self.timetable.save()
        matching_training = Training.objects.filter(
            day_of_week=6,
            skill_level=3,
            court=self.court1,
            start_time=datetime.time(20, 00, 00)
        ).first()
        self.assertIsNotNone(matching_training)
        self.assertEqual(
            Training.objects.get(pk=self.not_matching_training.pk).skill_level,
            2
        )

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_save_if_timetable_not_exist(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        Timetable.objects.create(
            day_of_week=5,
            skill_level=3,
            court=self.court1,
            start_time=datetime.time(16, 00, 00),
            active=True,
        )
        self.assertIsNotNone(Training.objects.filter(
            skill_level=3, day_of_week=5, court=self.court1).first())
        all_trainings = Training.objects.all()
        training_past = all_trainings.get(pk=self.training_past.pk)
        training_1 = all_trainings.get(pk=self.training_1.pk)
        self.assertEqual(training_past.skill_level, 1)
        self.assertEqual(training_past.start_time, datetime.time(18, 00, 00))
        self.assertEqual(training_1.start_time, datetime.time(18, 00, 00))
        self.assertEqual(training_1.skill_level, 1)

    @mock.patch('volleyballschool.models.datetime', wraps=datetime)
    def test_delete(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 10, 10)
        pk = self.timetable.pk
        self.timetable.delete()
        all_trainings = Training.objects.all()
        self.assertIsNone(Timetable.objects.filter(pk=pk).first())
        self.assertEqual(all_trainings.count(), 2)
        self.assertIn(self.training_past, all_trainings)
        self.assertIn(self.not_matching_training, all_trainings)

    def test_create_upcoming_trainings_if_not_active(self):
        self.timetable.active = False
        self.timetable.save()
        Training.objects.all().delete()
        self.timetable.create_upcoming_trainings()
        self.assertEqual(Training.objects.all().count(), 0)

    def test_create_upcoming_trainings_if_active(self):
        Training.objects.all().delete()
        self.assertEqual(Training.objects.all().count(), 0)
        self.timetable.create_upcoming_trainings()
        self.assertGreater(Training.objects.all().count(), 0)


class TimetableViewTests(TestCase):
    def test_skill_level_1_to_3(self):
        skill_levels_list = [
            'для начального уровня',
            'для уровня начальный+',
            'для среднего уровня'
        ]
        for i, level_name in enumerate(skill_levels_list, start=1):
            response = self.client.get(reverse('timetable', args=[i]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['skill_level'], level_name)

    def test_skill_level_wrong(self):
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse('timetable', args=[20]))

    def test_queryset_if_no_trainings(self):
        response = self.client.get(reverse('timetable', args=[2]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['trainings'], [])

    @mock.patch('volleyballschool.utils.datetime', wraps=datetime)
    def test_queryset_if_trainings(self, mocked_datetime):
        mocked_datetime.date.today.return_value = datetime.date(2020, 5, 20)
        court1 = Court.objects.create(passport_required=False, active=True)
        for i, j in ((5, 15), (2, 19), (4, 22), (2, 26), (4, 29), (7, 31)):
            Training.objects.create(
                day_of_week=i,
                skill_level=1,
                start_time=datetime.time(18, 00, 00),
                date=datetime.date(2020, 5, j),
                court=court1,
            )
        Training.objects.create(
                day_of_week=4,
                skill_level=2,
                start_time=datetime.time(18, 00, 00),
                date=datetime.date(2020, 5, 21),
                court=court1,
            )
        expected_result = [  # FOR number_of_weeks = 2 in TimetableView !!!
            {'name': court1,
             'weeks': [
                 [{'date': datetime.date(2020, 5, 18)},  # пн.
                  Training.objects.get(date=datetime.date(2020, 5, 19)),  # вт.
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
                  Training.objects.get(date=datetime.date(2020, 5, 29)),  # пт.
                  {'date': datetime.date(2020, 5, 30)},  # сб.
                  Training.objects.get(date=datetime.date(2020, 5, 31)),  # вс.
                  ],
             ]
             },
        ]
        response = self.client.get(reverse('timetable', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['trainings'], expected_result)


class BuyingASubscriptionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.subscription_sample = SubscriptionSample.objects.create(
            name='Абонемент на 4 занятия',
            amount=900,
            trainings_qty=4,
            validity=30,
            active=True
        )
        cls.url = reverse('buying-a-subscription',
                          args=[cls.subscription_sample.pk])
        cls.user = User.objects.create_user(username='test_user', balance=900)

    def setUp(self):
        self.client.force_login(self.user)

    def test_not_logged_in_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + f"?next={self.url}")

    def test_subscription_sample_not_exist(self):
        response = self.client.get(reverse('buying-a-subscription', args=[55]))
        self.assertEqual(response.status_code, 404)

    def test_subscription_sample_exist(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_buying_subscription(self):
        response = self.client.post(self.url, {'confirm': True})
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(self.user.balance, 0)
        self.assertEqual(self.user.subscriptions.count(), 1)
        self.assertTrue(self.client.session['submitted'])
        subscription = self.user.subscriptions.last()
        success_url = reverse('success-buying-a-subscription',
                              args=[subscription.id])
        self.assertRedirects(response, success_url)
        self.assertEqual(self.subscription_sample.trainings_qty,
                         subscription.trainings_qty)
        self.assertEqual(self.subscription_sample.validity,
                         subscription.validity)

    def test_buying_subscription_if_user_has_no_enough_money(self):
        self.user.balance = 899
        self.user.save(update_fields=['balance'])
        response = self.client.post(self.url, {'confirm': True})
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(self.user.balance, 899)
        self.assertEqual(self.user.subscriptions.count(), 0)
        self.assertNotIn('submitted', self.client.session)
        self.assertRedirects(response, self.url)


class SuccessBuyingASubscriptionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.user = User.objects.create_user(username='test_user')
        cls.subscription = Subscription.objects.create(
            active=True, user=cls.user, trainings_qty=2, validity=30)
        cls.url = reverse('success-buying-a-subscription',
                          args=[cls.subscription.pk])

    def setUp(self):
        self.client.force_login(self.user)

    def test_not_logged_in_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + f"?next={self.url}")

    def test_if_session_has_no_submitted_true(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('prices'))

    def test_if_session_has_submitted_true_and_subscription_not_exist(self):
        session = self.client.session
        session['submitted'] = True
        session.save()
        self.assertTrue(self.client.session['submitted'])
        response = self.client.get(
            reverse('success-buying-a-subscription', args=[55])
        )
        self.assertNotIn('submitted', self.client.session)
        self.assertEqual(response.status_code, 404)

    def test_session_has_submitted_true_but_subscription_owner_isnt_current_user(self):
        user2 = User.objects.create_user(username='test_user2')
        self.client.force_login(user2)
        session = self.client.session
        session['submitted'] = True
        session.save()
        self.assertTrue(self.client.session['submitted'])
        response = self.client.get(self.url)
        self.assertNotIn('submitted', self.client.session)
        self.assertRedirects(response, reverse('prices'))

    def test_session_has_submitted_true_and_subscription_exist(self):
        session = self.client.session
        session['submitted'] = True
        session.save()
        self.assertTrue(self.client.session['submitted'])
        response = self.client.get(self.url)
        self.assertNotIn('submitted', self.client.session)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subscription'], self.subscription)


class RegistrationForTrainingViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.court1 = Court.objects.create(passport_required=False, active=True)
        cls.price_for_one_training = OneTimeTraining.objects.create(price=900)

    def setUp(self):
        self.upcoming_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            date=datetime.date.today()+datetime.timedelta(days=2),
            start_time=datetime.time(18, 00, 00),
            court=self.court1,
        )
        self.user = User.objects.create_user(username='test_user', balance=900)
        self.url = reverse('registration-for-training',
                           args=[self.upcoming_training.pk])
        self.client.force_login(self.user)

    def test_not_logged_in_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + f"?next={self.url}")

    def test_training_not_exist(self):
        response = self.client.get(reverse('registration-for-training',
                                           args=[1030]))
        self.assertEqual(response.status_code, 404)

    def test_training_passed(self):
        past_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            date=datetime.date.today()-datetime.timedelta(days=2),
            start_time=datetime.time(18, 00, 00),
            court=self.court1,
        )
        response = self.client.get(reverse('registration-for-training',
                                           args=[past_training.pk]))
        self.assertEqual(response.status_code, 404)

    def test_context(self):
        subscription = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        response = self.client.get(self.url)
        self.assertNotIn('already_registered', response.context)
        self.assertEqual(response.context['subscription_of_user'],
                         subscription)
        self.assertEqual(response.context['price_for_one_training'],
                         self.price_for_one_training.price)
        self.assertEqual(response.status_code, 200)

    def test_context_if_user_already_registered_to_training(self):
        self.upcoming_training.learners.add(self.user)
        response = self.client.get(self.url)
        self.assertTrue(response.context['already_registered'])
        self.assertEqual(response.status_code, 200)

    def test_register_for_training_by_subscription(self):
        subscription = Subscription.objects.create(
            active=True, user=self.user, trainings_qty=2, validity=30)
        response = self.client.post(
            self.url, {'confirm': True, 'payment_by': 'subscription'})
        self.assertIn(self.user, self.upcoming_training.learners.all())
        self.assertIn(self.upcoming_training, subscription.trainings.all())
        self.assertRedirects(response, self.url)

    def test_register_for_training_by_user_balance(self):
        response = self.client.post(
            self.url, {'confirm': True, 'payment_by': 'balance'})
        self.user = User.objects.get(pk=self.user.pk)
        self.assertIn(self.user, self.upcoming_training.learners.all())
        self.assertEqual(self.user.balance, 0)
        self.assertRedirects(response, self.url)

    def test_cancel_registration_for_training(self):
        self.upcoming_training.learners.add(self.user)
        response = self.client.post(self.url, {'cancel': True})
        self.user = User.objects.get(pk=self.user.pk)
        self.assertNotIn(self.user, self.upcoming_training.learners.all())
        self.assertEqual(self.user.balance, 1800)
        self.assertRedirects(response, self.url)


class AccountViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.court1 = Court.objects.create(passport_required=False, active=True)
        cls.price_for_one_training = OneTimeTraining.objects.create(price=900)
        cls.upcoming_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            date=datetime.date.today()+datetime.timedelta(days=2),
            start_time=datetime.time(18, 00, 00),
            court=cls.court1,
        )
        cls.user = User.objects.create_user(username='test_user', balance=900)
        cls.subscription = Subscription.objects.create(
            active=True, user=cls.user, trainings_qty=2, validity=30)
        cls.not_active_sub = Subscription.objects.create(
            active=False, user=cls.user, trainings_qty=2, validity=30)
        cls.not_active_sub_2 = Subscription.objects.create(
            active=False, user=cls.user, trainings_qty=2, validity=30)
        cls.url = reverse('account')
        cls.not_active_sub.purchase_date = (
            datetime.date.today() - datetime.timedelta(days=41))
        cls.not_active_sub_2.purchase_date = (
            datetime.date.today() - datetime.timedelta(days=85))
        Subscription.objects.bulk_update(
            [cls.not_active_sub, cls.not_active_sub_2], ['purchase_date'])
        cls.upcoming_training.learners.add(cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def test_not_logged_in_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + f"?next={self.url}")

    def test_context(self):
        response = self.client.get(self.url)
        self.assertIn(self.upcoming_training,
                      response.context['user_upcoming_trainings'])
        self.assertEqual(response.context['user_upcoming_trainings'].count(),
                         1)
        self.assertEqual(response.context['user_active_subscriptions'],
                         [self.subscription])
        self.assertEqual(response.context['last_not_active_subscription'],
                         self.not_active_sub)
        self.assertEqual(response.status_code, 200)

    def test_cancel_registration_for_training(self):
        response = self.client.post(
            self.url, {'cancel': True, 'pk': self.upcoming_training.pk})
        self.user = User.objects.get(pk=self.user.pk)
        self.assertNotIn(self.user, self.upcoming_training.learners.all())
        self.assertEqual(self.user.balance, 1800)
        self.assertRedirects(response, self.url)
        self.upcoming_training.learners.add(self.user)
        User.objects.filter(pk=self.user.pk).update(balance=900)


class IndexViewTests(TestCase):
    def test_context(self):
        News.objects.bulk_create(
            [News(title='Новость{}'.format(i)) for i in range(4)])
        response = self.client.get(reverse('index_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['latest_news_list'].count(), 3)


class LevelsViewTests(TestCase):
    def test_template_used(self):
        response = self.client.get(reverse('levels'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'volleyballschool/levels.html')


class NewsViewTests(TestCase):
    def test_pagination(self):
        News.objects.bulk_create(
            [News(title='Новость{}'.format(i)) for i in range(5)])
        response = self.client.get(reverse('news'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['news_list'].count(), 4)
        response = self.client.get(reverse('news')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['news_list'].count(), 1)


class CoachesViewTests(TestCase):
    def test_context(self):
        coach1 = Coach.objects.create(name='Тренер1', active=True)
        Coach.objects.create(name='Тренер2', active=False)
        coach3 = Coach.objects.create(name='Тренер3', active=True)
        response = self.client.get(reverse('coaches'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(coach1, response.context['coaches_list'])
        self.assertIn(coach3, response.context['coaches_list'])
        self.assertEqual(response.context['coaches_list'].count(), 2)


class PricesViewTests(TestCase):
    def test_context(self):
        one_time_training = OneTimeTraining.objects.create(price=900)
        SubscriptionSample.objects.create(
            name='Абонемент1',
            amount=3000,
            trainings_qty=2,
            validity=30,
            active=False
        )
        sub_sample2 = SubscriptionSample.objects.create(
            name='Абонемент2',
            amount=3000,
            trainings_qty=2,
            validity=30,
            active=True
        )
        response = self.client.get(reverse('prices'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(sub_sample2, response.context['subscription_samples'])
        self.assertEqual(response.context['subscription_samples'].count(), 1)
        self.assertEqual(one_time_training,
                         response.context['one_time_training'])


class CourtsViewTests(TestCase):
    def test_context(self):
        Court.objects.create(
            name='Зал1',
            metro='Станция1',
            passport_required=False,
            active=False,
        )
        court2 = Court.objects.create(
            name='Зал2',
            metro='Станция2',
            passport_required=False,
            active=True,
        )
        response = self.client.get(reverse('courts'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(court2.metro, response.context['courts_metro_list'])
        self.assertEqual(response.context['courts_metro_list'].count(), 1)


class ArticlesViewTests(TestCase):
    def test_pagination(self):
        not_active_article = Article.objects.create(
            active=False, slug='NA', title='NA')
        Article.objects.bulk_create([
            Article(
                active=True,
                slug='article{}'.format(i),
                title='Статья{}'.format(i),
            ) for i in range(6)
        ])
        response = self.client.get(reverse('articles'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['articles_list'].count(), 5)
        self.assertNotIn(not_active_article, response.context['articles_list'])
        response = self.client.get(reverse('articles')+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['articles_list'].count(), 1)
        self.assertNotIn(not_active_article, response.context['articles_list'])


class ArticleDetailViewTests(TestCase):
    def test_template_used(self):
        article = Article.objects.create(
            active=True, slug='slug', title='test')
        response = self.client.get(reverse('article-detail', args=['slug']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['article'], article)
        self.assertTemplateUsed(response,
                                'volleyballschool/article_detail.html')

    def test_article_does_not_exist(self):
        response = self.client.get(reverse('article-detail', args=['any']))
        self.assertEqual(response.status_code, 404)

    def test_article_is_not_active(self):
        Article.objects.create(
            active=False, slug='slug', title='test')
        response = self.client.get(reverse('article-detail', args=['slug']))
        self.assertEqual(response.status_code, 404)


class RegisterUserViewTests(TestCase):
    def test_logged_in_user(self):
        user = User.objects.create_user(username='test_user')
        self.client.force_login(user)
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('account'))

    def test_template_used(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'volleyballschool/register.html')

    def test_register_user_form(self):
        response = self.client.post(reverse('register'))
        self.assertFormError(
            response, 'form', 'username', 'Обязательное поле.')
        self.assertFormError(
            response, 'form', 'first_name', 'Обязательное поле.')
        self.assertFormError(
            response, 'form', 'patronymic', 'Обязательное поле.')


class ReplenishmentViewTests(TestCase):
    def test_not_logged_in_user(self):
        response = self.client.get(reverse('replenishment'))
        self.assertRedirects(
            response, reverse('login') + f"?next={reverse('replenishment')}")

    def test_logged_in_user(self):
        user = User.objects.create_user(username='test_user')
        self.client.force_login(user)
        response = self.client.get(reverse('replenishment'))
        self.assertEqual(response.status_code, 200)
