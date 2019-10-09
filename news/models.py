import uuid

from accounts.models import CustomUser

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.urls import reverse

from urllib.parse import urlparse



class Item(MPTTModel):
    class Meta:
        indexes = [
            #models.Index(fields=['points', 'created_at']),
            models.Index(fields=['created_at', 'points']),
            models.Index(fields=['created_at', 'id']),
            models.Index(fields=['id', 'created_at']),
        ]
        # ordering = ['-created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    upvotes = models.PositiveIntegerField(default=0, editable=False)
    downvotes = models.PositiveIntegerField(default=0, editable=False)
    points = models.IntegerField(default=0, editable=False)
    num_comments = models.PositiveIntegerField(default=0, editable=False)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', editable=False)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE)

    is_ask = models.BooleanField(default=False)
    is_show = models.BooleanField(default=False)


    def get_absolute_url(self):
        return reverse("item", kwargs={"pk": self.pk})


    def can_be_upvoted_by(self, user):
        if not user.is_authenticated:
            return False
        if user == self.user:
            return False
        if Vote.objects.filter(user=user, item=self).count():
            return False
        return True
    
    def can_be_downvoted_by(self, user):
        if not user.is_authenticated:
            return False
        if user == self.user:
            return False
        else:
            if user.karma > 1:
                if not Vote.objects.filter(user=user, item=self).count():
                    return True
        return False

    def can_be_edited_by(self, user):
        return self.user == user and self.num_comments == 0
    
    def can_be_deleted_by(self, user):
        return self.can_be_edited_by(user)



class Story(Item):
    class Meta:
        indexes = [
            models.Index(fields=['domain', 'duplicate_of']),
        ]
    is_story = True

    # class Meta:
    #     ordering = ['-pk']
    title = models.CharField(max_length=255, blank=True)
    url = models.URLField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    duplicate_of = models.ForeignKey('Story', on_delete=models.CASCADE, null=True)
    domain = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    

    def __str__(self):
        return self.title
    
    # @property
    # def domain(self):
    #     o = urlparse(self.url)
    #     return o.hostname

    def can_be_downvoted_by(self, user):
        return False

    # def Kcomments(self):
    #     return self.comments
    #     return {
    #         'all': self.get_descendants() # lambda: [i.comment for i in self.get_descendants().select_related('comment')]
    #     }
    #     return self.comments


class Comment(Item):
    is_comment = True

    text = models.TextField()
    to_story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return self.text[:255]

    def comments(self):
        return {
            #'all': lambda: [i.comment for i in self.get_descendants().select_related('comment')]
            'all': lambda: [i.comment for i in self.get_descendants()]
        }


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    changed_at = models.DateTimeField(auto_now=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    # vote = None # -1 | 0 | 1 --> BooleanField(default=None, null=True)??
    vote = models.SmallIntegerField(default=1)
    user = models.ForeignKey(to=CustomUser, on_delete=models.CASCADE)


