from django.contrib.auth.models import AnonymousUser
from accounts.models import CustomUser
from django.test import RequestFactory, TestCase

from .views import *
from .models import *
from .forms import *

class BasicEmailDigestTest(TestCase):
    """Tests the basic functionality of the emaildigest app."""
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='sebst', email='hi@seb.st', password='top_secret')
        self.other_user = CustomUser.objects.create_user(
            username='bla1', email='two@seb.st', password='top_secret')

    def _subscribe(self, i=0):
        self.assertEqual(Subscription.objects.all().count(), 0+i)

        request = self.factory.post('/digest/subscribe', {'email': 'test@example.org'})
        request.user = self.user
        response = subscribe(request)

        #self.assertContains(response.url, 'thankyou')
        self.assertRegex(response.url, r'.*thankyou.*')

        self.assertEqual(Subscription.objects.all().count(), 1+i)

        subscription = Subscription.objects.all().order_by('-created_at')[0]
        self.assertFalse(subscription.is_active)

        verification_code = subscription.anonymoussubscription.verification_code

        return subscription

    def _confirm(self, subscription):
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.anonymoussubscription.verified)
        self.assertFalse(subscription.is_active)
        verification_code = subscription.anonymoussubscription.verification_code

        url = '/digest/subscribe?v=' + str(verification_code)

        request = self.factory.get(url)
        request.user = self.user
        response = subscribe(request)

        subscription = Subscription.objects.get(pk=subscription.pk)
        anonymoussubscription = AnonymousSubscription.objects.get(pk=subscription.pk)
        self.assertTrue(anonymoussubscription.verified)


    def _unsubscribe_via_mail(self, subscription, assert_form_error=False):
        subscription = Subscription.objects.get(pk=subscription.pk)

        self.assertEqual(UnSubscription.objects.all().count(), 0)

        url = '/digest/unsubscribe'
        request = self.factory.post(url, {'email': subscription.anonymoussubscription.email})
        request.user = self.user
        response = unsubscribe(request)
        if assert_form_error:
            # self.assertFormError(response, UnsunscribeForm, 'email', 'No subscription found for email ' + subscription.anonymoussubscription.email)
            self.assertContains(response, 'No subscription found for email')
            return None
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, r'.*done.*')

        self.assertEqual(UnSubscription.objects.all().count(), 1)

        unsubscription = UnSubscription.objects.get()
        return unsubscription


    def test_subscribe(self):
        subscription = self._subscribe()
        self.assertFalse(subscription.is_active)


    def test_subscribe_confirm(self):
        subscription = self._subscribe()
        self._confirm(subscription)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertTrue(subscription.is_active)


    def test_subscribe_unsubscribe(self):
        subscription = self._subscribe()
        unsubscription = self._unsubscribe_via_mail(subscription, assert_form_error=True)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.is_active)


    def test_subscribe_confirm_unsubscribe(self):
        subscription = self._subscribe()
        self._confirm(subscription)
        unsubscription = self._unsubscribe_via_mail(subscription)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.is_active)


    def test_subscribe_unsubscribe_confirm(self):
        subscription = self._subscribe()
        unsubscription = self._unsubscribe_via_mail(subscription, assert_form_error=True)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.is_active)

        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.is_active)

        self._confirm(subscription)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertTrue(subscription.is_active)


    def test_subscribe_confirm_unsubscribe_subscribe(self):
        subscription = self._subscribe()
        self._confirm(subscription)
        unsubscription = self._unsubscribe_via_mail(subscription)

        subscription2 = self._subscribe(i=1)
        subscription2 = Subscription.objects.get(pk=subscription2.pk)
        self.assertFalse(subscription.is_active)



    def test_subscribe_confirm_unsubscribe_subscribe_confirm(self):
        subscription = self._subscribe()
        self._confirm(subscription)
        
        unsubscription = self._unsubscribe_via_mail(subscription)

        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertFalse(subscription.is_active)

        re_subscription = self._subscribe(i=1)
        self._confirm(re_subscription)

        re_subscription = Subscription.objects.get(pk=re_subscription.pk)
        subscription = Subscription.objects.get(pk=subscription.pk)
        self.assertTrue(re_subscription.is_active)
        self.assertFalse(subscription.is_active)



# class ReceiversEmailDigestTest(TestCase):
#     """Tests the basic receivers functionality of the emaildigest app."""
#     def setUp(self):
#         # Every test needs access to the request factory.
#         self.factory = RequestFactory()
#         self.user = CustomUser.objects.create_user(
#             username='sebst', email='hi@seb.st', password='top_secret')
#         self.other_user = CustomUser.objects.create_user(
#             username='bla1', email='two@seb.st', password='top_secret')


#     def test_lower_email_addresses(self):
#         self.fail()

#     def activate_subscription_on_verification(self):
#         self.fail()

#     def test_on_subscription_created(self):
#         self.fail()

#     def test_on_unsubscription_created(self):
#         self.fail()