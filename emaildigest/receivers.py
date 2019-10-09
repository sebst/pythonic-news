#from django.core.signals import request_finished
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives



from .models import UserSubscription, AnonymousSubscription, Subscription, UnSubscription


@receiver(pre_save)
def lower_email_addresses(sender, instance, **kwargs):
    if isinstance(instance, (UserSubscription, AnonymousSubscription)):
        if isinstance(instance, AnonymousSubscription):
            instance.email = instance.email.lower()
    if isinstance(instance, Subscription):
        if instance.verfied_email:
            instance.verfied_email = instance.verfied_email.lower()


@receiver(post_save)
def activate_subscription_on_verification(sender, instance, created, **kwargs):
    if isinstance(instance, AnonymousSubscription):
        if instance.verified:
            subscription = instance.subscription_ptr
            subscription.is_active = True
            subscription.verfied_email = instance.email
            subscription.save()

@receiver(post_save)
def on_subscription_created(sender, instance, created, **kwargs):
    if created and isinstance(instance, (UserSubscription, AnonymousSubscription)):
        subscription = instance


@receiver(post_save)
def on_unsubscription_created(sender, instance, created, **kwargs):
    if created and isinstance(instance, (UnSubscription)):
        unsubscription = instance
        unsubscription.subscription.is_active = False
        unsubscription.subscription.save()