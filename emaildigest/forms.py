from django import forms

from .models import UserSubscription, AnonymousSubscription, Subscription


class UserSubscriptionForm(forms.ModelForm):
    thankyou = 'u'
    class Meta:
        model = UserSubscription
        fields = []


class AnonymousSubscriptionForm(forms.ModelForm):
    thankyou = 'a'
    class Meta:
        model = AnonymousSubscription
        fields = ['email']
    
    def clean_email(self):
        data = self.cleaned_data['email']
        if data:
            data = data.lower()
        return data


def validate_active_email(email):
    qs = Subscription.objects.filter(verfied_email=email, is_active=True)
    if not qs.count():
        raise forms.ValidationError(
            ('No subscription found for email %(email)s'),
            code='invalid',
            params={'email': email},)

class UnsunscribeForm(forms.Form):
    email = forms.EmailField(validators=[validate_active_email])

    def clean_email(self):
        data = self.cleaned_data['email']
        if data:
            data = data.lower()
        return data


def get_subscription_form(user, *args, **kwargs):
    return AnonymousSubscriptionForm(*args, **kwargs)
    if user.is_authenticated:
        return UserSubscriptionForm(*args, **kwargs)
    else:
        return AnonymousSubscriptionForm(*args, **kwargs)