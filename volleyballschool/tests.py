import datetime

from volleyballschool.models import Court, Subscription, Training, User
from django.test import TestCase


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
