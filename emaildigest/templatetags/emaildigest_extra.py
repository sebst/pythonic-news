from django import template

register = template.Library()

from emaildigest.forms import get_subscription_form

@register.inclusion_tag('emaildigest/_subscription_form_tag.html')
def digest_subscription_form(user, **kwargs):
    form = get_subscription_form(user)
    return {'subscription_form': form}
