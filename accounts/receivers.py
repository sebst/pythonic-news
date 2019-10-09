#from django.core.signals import request_finished
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

from django.conf import settings



from .models import CustomUser, Invitation, EmailVerification, PasswordResetRequest


@receiver(pre_save)
def lower_email_addresses(sender, instance, **kwargs):
    if isinstance(instance, CustomUser):
        email = getattr(instance, 'email', None)
        if email:
            instance.email = email.lower()


@receiver(post_save)
def send_invitation_email(sender, instance, created, **kwargs):
    if created and isinstance(instance, Invitation):
        subject, from_email, to = 'You have been invited to %s'%(settings.SITE_DOMAIN), 'bot@python.sc', instance.invited_email_address
        text_content = """
You have been invited to news.python.sc.

Would you like to accept {inviting_user}'s invite?

Please sign up here: https://news.python.sc{url}

-- 
news.python.sc - A social news aggregator for the Python community.

""".format(inviting_user=instance.inviting_user.username, url=instance.get_register_url())
        #html_content = '<p>This is an <strong>important</strong> message.</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        #msg.attach_alternative(html_content, "text/html")
        msg.send()


@receiver(post_save)
def create_verification(sender, instance, created, **kwargs):
    if isinstance(instance, CustomUser):
        if instance.email:
            verifications = EmailVerification.objects.filter(user=instance, email=instance.email)
            if not verifications.count():
                create_v = True
            else:
                verified = any([i.verified for i in verifications])
                # create_v = not verified
                create_v = False
            
            if create_v:
                verification = EmailVerification(user=instance, email=instance.email)
                verification.save()


@receiver(post_save)
def send_verification_email(sender, instance, created, **kwargs):
    if created and isinstance(instance, EmailVerification):
        subject, from_email, to = 'Please confirm your account on news.python.sc', 'bot@python.sc', instance.email
        text_content = """
Please confirm your email address here:

https://news.python.sc{url}

-- 
news.python.sc - A social news aggregator for the Python community.

""".format(url=instance.get_verify_url())
        #html_content = '<p>This is an <strong>important</strong> message.</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        #msg.attach_alternative(html_content, "text/html")
        msg.send()


@receiver(post_save)
def send_password_reset_email(sender, instance, created, **kwargs):
    if created and isinstance(instance, PasswordResetRequest):
        subject, from_email, to = 'Reset password for your account on news.python.sc', 'bot@python.sc', instance.email
        text_content = """
Please confirm your email address here:

https://news.python.sc{url}

-- 
news.python.sc - A social news aggregator for the Python community.

""".format(url=instance.get_verify_url())
        #html_content = '<p>This is an <strong>important</strong> message.</p>'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        #msg.attach_alternative(html_content, "text/html")
        msg.send()