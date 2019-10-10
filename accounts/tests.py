from django.contrib.auth.models import AnonymousUser
from accounts.models import CustomUser
from django.test import RequestFactory, TestCase

from .views import *
from .models import *

class BasicAccountsTest(TestCase):
    """Tests the basic functionality of the accounts app."""
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='sebst', email='hi@seb.st', password='top_secret')
        self.other_user = CustomUser.objects.create_user(
            username='bla1', email='two@seb.st', password='top_secret')


class ReceiversAccountsTest(TestCase):
    """Tests the basic functionality of the accounts app."""
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='sebst', email='hi@seb.st', password='top_secret')
        self.other_user = CustomUser.objects.create_user(
            username='bla1', email='two@seb.st', password='top_secret')


    def test_lower_email_addresses(self):
        user = CustomUser.objects.create_user(
            username='johndoe', email='J.Doe@exAmple.org', password='top_secret')
        user = CustomUser.objects.get(pk=user.pk)
        self.assertEqual(user.email, 'j.doe@example.org')


    def test_send_invitation_email(self):
        self.skipTest()
        self.assertTrue(False)


    def test_create_verification(self):
        user = CustomUser.objects.create_user(
            username='johndoe', email='J.Doe@exAmple.org', password='top_secret')
        verification = EmailVerification.objects.get(user=user, email=user.email)
        self.assertEqual(verification.email, user.email)
        self.assertEqual(verification.email, 'j.doe@example.org')



    def test_send_verification_email(self):
        self.skipTest()
        self.assertTrue(False)


    def test_send_password_reset_email(self):
        self.skipTest()
        self.assertTrue(False)
