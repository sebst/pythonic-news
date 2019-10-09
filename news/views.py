from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Item, Story, Comment, Vote
from accounts.models import CustomUser
from .forms import CommentForm, AddStoryForm, StoryForm

from ratelimit.decorators import ratelimit


# create_story
# add_comment
# upvote / downvote / unvote
# flag / hide
# Tags?
# suggest changes
# save


DEFAULT_GET_RATE   = "2/s"
DEFAULT_VOTES_RATE = "10/m"
DEFAULT_POST_RATE  = "5/m"

TIMEOUT_MEDIUM = 0# 1*60 # one minute
TIMEOUT_SHORT  = 0# 1*2 # two seconds


from django.db.models.functions import Power, Now, Cast, Extract #, Min
from django.db.models import Value, F, Func, ExpressionWrapper, fields, Q, Min
from django.db.models import OuterRef, Subquery
from django.db import models
from django.utils import timezone
import datetime

from django.core.cache import cache
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_page

from django.db import connection


def _one_page_back(request):
    page = int(request.GET.get('p', 0))
    query_dict = request.GET.copy()
    page = page - 1
    if page >= 0:
        query_dict['p'] = page
    else:
        return None
    _more_link=request.path_info + '?' + query_dict.urlencode()
    return HttpResponseRedirect(_more_link)

def _front_page(paging_size=settings.PAGING_SIZE, page=0, add_filter={}, add_q=[], as_of=None, days_back=50):
    # TODO: weighting https://medium.com/hacking-and-gonzo/how-hacker-news-ranking-algorithm-works-1d9b0cf2c08d
    # (P-1) / (T+2)^G
    if as_of is None:
        now = timezone.now()
    else:
        now = as_of
    if connection.vendor == 'postgresql':
        now_value = Value(now, output_field=fields.DateTimeField())
        submission_age_float = ExpressionWrapper(  ( now_value - F('created_at')), output_field=fields.DurationField())
        submission_age_hours = ExpressionWrapper(Extract(F('tf'), 'epoch') / 60 / 60 + 2.1 , output_field=fields.FloatField())
        real_p = ExpressionWrapper(F('points') - 1, output_field=fields.FloatField())
        formula = ExpressionWrapper(   F('p') / ( Power(F('tfh'), F('g'))  +0.001)   , output_field=fields.FloatField())
        return Story.objects.select_related('user')\
                .filter(duplicate_of__isnull=True)\
                .filter(points__gte=1) \
                .filter(created_at__gte=now - datetime.timedelta(days=days_back)) \
                .filter(created_at__lte=now) \
                .filter(**add_filter) \
                .annotate(tf=submission_age_float) \
                .annotate(tfh=submission_age_hours) \
                .annotate(p=real_p) \
                .annotate(g=Value(1.8, output_field=fields.FloatField())) \
                .annotate(formula=formula) \
                .order_by('-formula')[(page*paging_size):(page+1)*(paging_size)]
    elif connection.vendor == 'sqlite':
        now_value = Value(now, output_field=fields.DateTimeField())
        submission_age_float = ExpressionWrapper(  ( now_value - F('created_at')), output_field=fields.FloatField())
        submission_age_hours = ExpressionWrapper(F('tf') / 60 / 60 / 1000000 + 2.1 , output_field=fields.FloatField())
        real_p = ExpressionWrapper(F('points') - 1, output_field=fields.FloatField())
        formula = ExpressionWrapper(   F('p') / ( Power(F('tfh'), F('g'))  +0.001)   , output_field=fields.FloatField())
        return Story.objects.select_related('user')\
                .filter(duplicate_of__isnull=True)\
                .filter(points__gte=1) \
                .filter(created_at__gte=now - datetime.timedelta(days=days_back)) \
                .filter(created_at__lte=now) \
                .filter(**add_filter) \
                .annotate(tf=submission_age_float) \
                .annotate(tfh=submission_age_hours) \
                .annotate(p=real_p) \
                .annotate(g=Value(1.8, output_field=fields.FloatField())) \
                .annotate(formula=formula) \
                .order_by('-formula')[(page*paging_size):(page+1)*(paging_size)]
    else: 
        raise NotImplementedError("No frontpage magic for database engine %s implemented"%(connection.vendor))


def _newest(paging_size=settings.PAGING_SIZE, page=0, add_filter={}, add_q=[]):
    return Story.objects \
                .select_related('user') \
                .filter(duplicate_of__isnull=True) \
                .filter(**add_filter) \
                .filter(*add_q) \
                .order_by('-created_at')[(page*paging_size):(page+1)*(paging_size)]


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
def index(request):
    page = int(request.GET.get('p', 0))
    stories = cache.get_or_set("news-index-%s"%(page), lambda: list(_front_page(page=page)), timeout=TIMEOUT_MEDIUM) # one minute
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':True, 'page': page, 'rank_start': page*settings.PAGING_SIZE})


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
def show(request):
    page = int(request.GET.get('p', 0))
    stories = cache.get_or_set("news-show-%s"%(page), lambda: list(_front_page(page=page, add_filter={'is_show': True})), timeout=TIMEOUT_MEDIUM) # one minute
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':True, 'page': page, 'rank_start': page*settings.PAGING_SIZE})


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
def ask(request):
    page = int(request.GET.get('p', 0))
    stories = lambda: list(_front_page(page=page, add_filter={'is_ask': True}))
    stories = cache.get_or_set("news-ask-%s"%(page), stories, timeout=TIMEOUT_MEDIUM) # one minute
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':True, 'page': page, 'rank_start': page*settings.PAGING_SIZE})


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
def newest(request): # Done
    page = int(request.GET.get('p', 0))
    add_filter = {}
    add_q = []
    if 'submitted_by' in request.GET.keys():
        try:
            submitted_by = CustomUser.objects.get_by_natural_key(request.GET['submitted_by'])
            add_filter['user'] = submitted_by
        except CustomUser.DoesNotExist:
            raise Http404()
    if 'upvoted_by' in request.GET.keys():
        try:
            assert request.user.is_authenticated
            assert request.user.username == request.GET['upvoted_by']
        except AssertionError:
            return HttpResponseForbidden()
        add_filter['pk__in'] = Vote.objects.filter(vote=1, user=request.user).values('item')
        add_q.append(~Q(user=request.user))
    if 'site' in request.GET.keys():
        add_filter['domain'] = request.GET['site']
    stories = lambda: list(_newest(page=page, add_filter=add_filter, add_q=add_q))
    stories = cache.get_or_set("news-newest-%s"%(page), stories, timeout=TIMEOUT_SHORT) # two seconds
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':True, 'page': page, 'rank_start': page*settings.PAGING_SIZE})


@login_required
@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
@cache_page(TIMEOUT_SHORT)
@vary_on_cookie
def threads(request):
    page = int(request.GET.get('p', 0))
    paging_size = settings.PAGING_SIZE
    tree = Comment.objects.filter( tree_id=OuterRef('tree_id'), user=OuterRef('user')).values('tree_id', 'user__pk').annotate(min_level=Min('level')).order_by()
    stories = Comment.objects.filter(
        user=request.user
    ).filter(
        Q(level__in=Subquery(tree.values('min_level'), output_field=models.IntegerField()))  # TODO: level= or level__in= ???
    ).select_related(
        'user', 'parent', 'to_story'
    ).order_by(
        '-created_at'
    )[(page*paging_size):(page+1)*(paging_size)]
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':False, 'page': page, 'rank_start': None, 'show_children': True})


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
@cache_page(TIMEOUT_SHORT)
@vary_on_cookie
def comments(request): # TODO
    page = int(request.GET.get('p', 0))
    paging_size = settings.PAGING_SIZE
    add_filter = {}
    if 'submitted_by' in request.GET.keys():
        try:
            submitted_by = CustomUser.objects.get_by_natural_key(request.GET['submitted_by'])
            add_filter['user'] = submitted_by
        except CustomUser.DoesNotExist:
            raise Http404()
    if 'upvoted_by' in request.GET.keys():
        try:
            assert request.user.is_authenticated
            assert request.user.username == request.GET['upvoted_by']
        except AssertionError:
            return HttpResponseForbidden()
        add_filter['pk__in'] = Vote.objects.filter(vote=1, user=request.user).values('item')
    stories = Comment.objects.filter(
        parent=None
    ).filter(
        **add_filter
    ).select_related(
        'user', 'parent', 'to_story'
    ).order_by(
        'created_at'
    )[(page*paging_size):(page+1)*(paging_size)]
    if len(stories) < 1 and page != 0:
        back = _one_page_back(request)
        if back:
            return back
    return render(request, 'news/index.html', {'stories': stories, 'hide_text':False, 'page': page, 'rank_start': page*paging_size})


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, block=True)
def zen(request):
    return render(request, 'news/zen.html')


def _vote(request, pk, vote=None, unvote=False):
    assert not unvote and vote is not None or unvote and vote is None
    item = get_object_or_404(Item, pk=pk)
    if (not unvote) and (vote is not None):
        votes = Vote.objects.filter(item=item, user=request.user)
        if request.method=="POST":
            if vote > 0:
                if not item.can_be_upvoted_by(request.user):
                    return HttpResponseForbidden()
            else:
                if not item.can_be_downvoted_by(request.user):
                    return HttpResponseForbidden()
            vote = Vote(vote=vote, item=item, user=request.user)
            vote.save()
            return HttpResponse("OK %s"%(vote.pk))
    if unvote:
        if request.method=="POST":
            Vote.objects.filter(item=item, user=request.user).delete()
            return HttpResponse("OK")


@login_required
@ratelimit(key="user_or_ip", group="news-votes", rate=DEFAULT_VOTES_RATE, block=True)
def upvote(request, pk):
    return _vote(request, pk, vote=1)


@login_required
@ratelimit(key="user_or_ip", group="news-votes", rate=DEFAULT_VOTES_RATE, block=True)
def downvote(request, pk):
    return _vote(request, pk, vote=-1)


@login_required
@ratelimit(key="user_or_ip", group="news-votes", rate=DEFAULT_VOTES_RATE, block=True)
def unvote(request, pk):
    return _vote(request, pk, vote=None, unvote=True)


def flag(request):
    pass


def save(request):
    pass


def _item_story_comment(pk):
    try: 
        # .prefetch_related('children', 'parent')
        item = Item.objects.select_related('story', 'comment', 'user', 'parent').prefetch_related('children').get(pk=pk)
    except Exception as e:
        raise e
    try:
        story = item.story
        comment = None
        item = story
    except Item.story.RelatedObjectDoesNotExist:
        story = None
        comment = None
    try:
        comment = item.comment
        story = comment.to_story
        item = comment
    except Item.comment.RelatedObjectDoesNotExist:
        pass
    assert story is not None
    return item, story, comment


@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, method=['GET'], block=True)
@ratelimit(key="user_or_ip", group="news-post", rate=DEFAULT_POST_RATE, method=['POST'], block=True)
def item(request, pk): # DONE
    item, story, comment = _item_story_comment(pk)
    if story == item:
        if story.duplicate_of is not None:
            return HttpResponseRedirect(story.duplicate_of.get_absolute_url())
    if request.user.is_authenticated:
        parent = None if story==item else item
        comment_instance = Comment(user=request.user, to_story=story, parent=parent)
        comment_form = CommentForm(request.POST or None, instance=comment_instance)
        if request.method == 'POST':
            if comment_form.is_valid():
                comment = comment_form.save()
                return HttpResponseRedirect(story.get_absolute_url() + '#' + str(comment.pk))
    else:
        comment_form = None
    return render(request, 'news/item.html', {'item': item, 'comment_form': comment_form})


@login_required
@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, method=['GET'], block=True)
@ratelimit(key="user_or_ip", group="news-post", rate=DEFAULT_POST_RATE, method=['POST'], block=True)
def item_edit(request, pk):
    item, story, comment = _item_story_comment(pk)
    if not item.can_be_edited_by(request.user):
        return HttpResponseForbidden()
    if story == item:
        if story.duplicate_of is not None:
            return HttpResponseRedirect(story.duplicate_of.get_absolute_url())
    if comment is not None:
        form = CommentForm(request.POST or None, instance=item)
    else:
        assert story is not None
        form = StoryForm(request.POST or None, instance=item)
    assert form is not None
    if request.method=="POST":
        if form.is_valid():
            item = form.save()
            return HttpResponseRedirect(story.get_absolute_url() + '#' + str(item.pk))
    return render(request, 'news/item_edit.html', {'item': item, 'edit_form': form})


@login_required
@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, method=['GET'], block=True)
@ratelimit(key="user_or_ip", group="news-post", rate=DEFAULT_POST_RATE, method=['POST'], block=True)
def item_delete(request, pk):
    item, story, comment = _item_story_comment(pk)
    if not item.can_be_deleted_by(request.user):
        return HttpResponseForbidden()
    if request.method == "POST":
        redirect_url = '/'
        if comment is not None:
            redirect_url = item.to_story.get_absolute_url()
        item.delete()
        return HttpResponseRedirect(redirect_url)
    return render(request, 'news/item_delete.html', {'item': item})


@login_required
@ratelimit(key="user_or_ip", group="news-get", rate=DEFAULT_GET_RATE, method=['GET'], block=True)
@ratelimit(key="user_or_ip", group="news-post", rate=DEFAULT_POST_RATE, method=['POST'], block=True)
def submit(request): # DONE
    instance = Story(user=request.user)
    form = AddStoryForm(request.POST or None, initial={
        'title': request.GET.get('t'),
        'url': request.GET.get('u'),
        'text': request.GET.get('x'),
    }, instance=instance)
    if request.method=="POST":
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(instance.get_absolute_url())
    return render(request, 'news/submit.html', {'form': form})


def robots_txt(request):
    return HttpResponse("""
User-agent: *
Disallow: 
    """, content_type='text/plain')

def humans_txt(request):
    return HttpResponse("""
🐍
    """, content_type='text/plain', charset='utf-8')


def bookmarklet(request):
    return render(request, 'news/bookmarklet.html')