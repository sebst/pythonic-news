from django.urls import path, include

from . import views




urlpatterns = [
    #path('profile', views.profile, name="accounts_my_profile"),
    path('subscribe', views.subscribe, name="emaildigest_subscribe"),
    path('subscriptions', views.my_subscriptions, name="emaildigest_subscriptions"),

    path('unsubscribe', views.unsubscribe, name='emaildigest_unsubscribe'),
    path('unsubscribe/<uuid:subscription_id>/<uuid:digest_id>', views.unsubscribe, name='emaildigest_unsubscribe'),

]
