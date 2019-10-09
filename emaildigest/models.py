import uuid
from django.db import models

class EmailDigest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)

    frequency = models.CharField(max_length=16, choices=(('weekly', 'weekly'), ('daily', 'daily')))
    weekly_weekday = models.CharField(max_length=16, null=True, blank=True, choices=(('Sun', 'Sun'), 
                                                                                     ('Mon', 'Mon'),
                                                                                     ('Tue', 'Tue'),
                                                                                     ('Wed', 'Wed'),
                                                                                     ('Thu', 'Thu'),
                                                                                     ('Fri', 'Fri'),
                                                                                     ('Sat', 'Sat')))
    stories = models.ManyToManyField('news.Story')

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    frequency = models.CharField(max_length=16, choices=(('weekly', 'weekly'), ('daily', 'daily')))
    weekly_weekday = models.CharField(max_length=16, null=True, blank=True, choices=(('Sun', 'Sun'), 
                                                                                     ('Mon', 'Mon'),
                                                                                     ('Tue', 'Tue'),
                                                                                     ('Wed', 'Wed'),
                                                                                     ('Thu', 'Thu'),
                                                                                     ('Fri', 'Fri'),
                                                                                     ('Sat', 'Sat')))
    verfied_email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=False)


class UserSubscription(Subscription):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True)


class AnonymousSubscription(Subscription):
    email = models.EmailField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True)
    verification_code = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    logged_in_user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, null=True)


class UnSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    from_digest = models.ForeignKey(EmailDigest, on_delete=models.CASCADE, null=True)