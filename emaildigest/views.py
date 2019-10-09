from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from .forms import get_subscription_form, UnsunscribeForm

from .models import AnonymousSubscription, UnSubscription, Subscription, EmailDigest


def subscribe(request):
    form = get_subscription_form(request.user, request.POST or None)
    thankyou = request.GET.get('thankyou', None)
    if thankyou:
        return render(request, 'emaildigest/subscribe_thankyou_%s.html'%(thankyou), {'prevent_footer_subscription_form': True})
    verification_code = request.GET.get('v', None)
    if verification_code:
        subscription = get_object_or_404(AnonymousSubscription, verification_code=verification_code)
        if not subscription.verified:
            subscription.verified = True
            subscription.verified_at = timezone.now()
            subscription.save()
        # TODO: Verify User account if needed # TODO: Activate usage of get_subsciption_form
        return render(request, 'emaildigest/subscribe_verification_done.html', {'prevent_footer_subscription_form': True})
    if request.method=="POST":
        if form.is_valid():
            subscription = form.save()
            if request.user.is_authenticated:
                subscription.logged_in_user = request.user
                subscription.save()
            return HttpResponseRedirect(reverse('emaildigest_subscribe') + '?thankyou=' + form.thankyou)
    return render(request, 'emaildigest/subscribe.html', {'subscription_form': form, 'prevent_footer_subscription_form': True})


def unsubscribe(request, subscription_id=None, digest_id=None):
    if 'done' in request.GET.keys():
        email = request.GET.get('email', None)
        suscription = request.GET.get('subscription', None)
        return render(request, 'emaildigest/unsubscribe_done.html', {'email': email, 'subscription': subscription, 'prevent_footer_subscription_form': True})
    if subscription_id is None and digest_id is None:
        form = UnsunscribeForm(request.POST or None)
        if request.method=="POST":
            if form.is_valid():
                email = form.cleaned_data['email']
                subscriptions = Subscription.objects.filter(verfied_email=email, is_active=True)
                for subscription in subscriptions:
                    unsubscription = UnSubscription(subscription=subscription)
                    unsubscription.save()
                return HttpResponseRedirect(reverse('emaildigest_unsubscribe') + "?done&email="+email)
        return render(request, 'emaildigest/unsubscribe.html', {'form': form, 'prevent_footer_subscription_form': True})
    elif subscription_id is not None and digest_id is not None:
        subscription = get_object_or_404(Subscription, pk=subscription_id)
        digest = get_object_or_404(EmailDigest, pk=digest_id)
        if request.method=="GET":
            return render(request, 'emaildigest/unsubscribe_confirm.html', {})
        elif request.method=="POST":
            unsubscription = UnSubscription(subscription=subscription, from_digest=digest)
            unsubscription.save()
            return HttpResponseRedirect(reverse('emaildigest_unsubscribe') + "?done&subscription="+subscription_id)
        else:
            return HttpResponseRedirect(reverse('emaildigest_unsubscribe'))
    else:
        return HttpResponseRedirect(reverse('emaildigest_unsubscribe'))
    pass


def my_subscriptions(request):
    return render(request, 'emaildigest/my_subscriptions.html')