from django import template
from django.utils.safestring import mark_safe

import mistune

register = template.Library()

@register.inclusion_tag('news/_item_tag.html', takes_context=True)
def news_item(context, item, **kwargs):
    kwargs['item'] = item
    kwargs['request_user'] = context['user']
    return kwargs

@register.inclusion_tag('news/_link_user_tag.html')
def link_user(user):
    return {
        'user': user
    }

@register.simple_tag
def user_arrows(user, item):
    if user == item.user:
        return ['star']
    else:
        res = []
        if item.can_be_upvoted_by(user=user):
            res.append('up')
        if item.can_be_downvoted_by(user=user):
            res.append('down')
        return res


@register.inclusion_tag('news/_more_link_tag.html', takes_context=True)
def more_link(context):
    request = context.request
    page = int(request.GET.get('p', 0))
    query_dict = request.GET.copy()
    query_dict['p'] = page + 1
    _more_link=request.path_info + '?' + query_dict.urlencode()
    return {'more_link': _more_link}


@register.inclusion_tag('news/_item_content_tag.html')
def item_content(**kwargs):
    return kwargs


@register.inclusion_tag('news/_item_control_tag.html')
def item_control(**kwargs):
    return kwargs

#renderer = mistune.Renderer(escape=True, hard_wrap=True)

class MarkdownRenderer(mistune.Renderer):

    @classmethod
    def setup(cls):
        renderer = cls(escape=True, hard_wrap=True)
        return mistune.Markdown(renderer=renderer)

    def header(self, text, level, raw=None):
        level = min(level + 2, 6)
        return super().header(text, level, raw)


markdown = MarkdownRenderer.setup()

@register.filter
def comment_markdown(value):
    return mark_safe(markdown(value))
