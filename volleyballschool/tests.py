import datetime

from volleyballschool.models import Court, Subscription, Training, User
from django.test import TestCase


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
            start_time='18:00:00',
            date=(cls.today-datetime.timedelta(days=1)),
            court=cls.court1,
        )
        cls.future_training = Training.objects.create(
            day_of_week=1,
            skill_level=1,
            start_time='18:00:00',
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
