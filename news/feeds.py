from django.contrib.syndication.views import Feed
from .models import Story
from .views import _newest, _front_page

from django.conf import settings

class NewestFeed(Feed):
    title = "%s: Latest"%(settings.SITE_NAME)
    link = "/newest/"
    description = "Latest stories"

    def items(self):
        return _newest(30, 0)

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.created_at
    
    def item_updateddate(self, item):
        return item.changed_at
    
    def item_author_name(self, item):
        return str(item.user)
    
    def item_author_link(self, item):
        return settings.SITE_URL + item.user.get_absolute_url()

    def item_description(self, item):
        return "TODO" # TODO
        return item.url


class FrontPageFeed(NewestFeed):
    title = "%s: Front Page" % (settings.SITE_NAME)
    link = "/feed"
    description = "Front Page stories"

    def items(self):
        return _front_page(30, 0)