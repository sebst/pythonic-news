from django.contrib.auth.models import AnonymousUser
from accounts.models import CustomUser
from django.test import RequestFactory, TestCase

from .views import *
from .models import *

class BasicNewsTest(TestCase):
    """Tests the basic functionality of the news app."""
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='sebst', email='hi@seb.st', password='top_secret')
        self.other_user = CustomUser.objects.create_user(
            username='bla1', email='two@seb.st', password='top_secret')
        
    def test_submit_get(self):
        """The submit form is displayed."""
        request = self.factory.get('/submit')
        request.user = self.user
        response = submit(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form')
    
    def test_submit_post_with_title_and_url(self):
        """Submission is posted with title and URL."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.user
        response = submit(request)
        self.assertEqual(response.status_code, 302)

    def test_submit_post_with_title_without_url(self):
        """Submission with only title should fail."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf'})
        request.user = self.user
        response = submit(request)
        self.assertEqual(response.status_code, 200)

    def test_submit_and_frontpage_and_newest(self):
        """A submission should appear on frontpage (as we have an empty database) and on the newest page."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.user
        response = submit(request)

        request = self.factory.get('/')
        request.user = self.user
        response = index(request)

        self.assertContains(response, 'test-post-asdf')


        request = self.factory.get('/newest')
        request.user = self.user
        response = index(request)

        self.assertContains(response, 'test-post-asdf')

    def test_submit_and_upvote(self):
        """A submission can be upvoted."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.other_user
        response = submit(request)
        item_url = response.url
        pk = item_url.split('/')[-1]

        upvote_url = item_url + "/upvote"

        request = self.factory.post(upvote_url, {})
        request.user = self.user
        response = upvote(request, pk=pk)
        self.assertContains(response, "OK")

        item = Item.objects.get(pk=pk)
        self.assertEqual(item.upvotes, 2)
        self.assertEqual(item.points, 2)
        #self.assertEqual(self.other_user.karma, 1) # Karma of submitting user should have increased
        self.assertEqual(item.user.karma, 1) # Karma of submitting user should have increased
        self.assertEqual(CustomUser.objects.get(pk=self.user.pk).karma, 0) # Karma of voting user should have stayed the same

    def test_submit_and_upvote_and_unvote(self):
        """A submission can be upvoted."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.other_user
        response = submit(request)
        item_url = response.url
        pk = item_url.split('/')[-1]

        upvote_url = item_url + "/upvote"

        request = self.factory.post(upvote_url, {})
        request.user = self.user
        response = upvote(request, pk=pk)
        self.assertContains(response, "OK")

        item = Item.objects.get(pk=pk)
        self.assertEqual(item.upvotes, 2)
        self.assertEqual(item.points, 2)
        #self.assertEqual(self.other_user.karma, 1) # Karma of submitting user should have increased
        self.assertEqual(item.user.karma, 1) # Karma of submitting user should have increased
        self.assertEqual(CustomUser.objects.get(pk=self.user.pk).karma, 0) # Karma of voting user should have stayed the same

        self.fail() # TODO: Test unvote


    def test_submit_and_downvote(self):
        """A submission cannot be downvoted."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf-12', 'url': 'https://sebastiansteins.com/12'})
        request.user = self.other_user
        response = submit(request)
        item_url = response.url
        pk = item_url.split('/')[-1]

        vote_url = item_url + "/downvote"

        request = self.factory.post(vote_url, {})
        request.user = self.user
        response = downvote(request, pk=pk)
        self.assertEqual(response.status_code, 403)


    def test_submit_and_upvote_self(self):
        """A submission cannot be upvoted by the submitting user."""
        request = self.factory.post('/submit', {'title': 'test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.user
        response = submit(request)
        item_url = response.url
        pk = item_url.split('/')[-1]

        upvote_url = item_url + "/upvote"

        request = self.factory.post(upvote_url, {})
        request.user = self.user
        response = upvote(request, pk=pk)
        self.assertEqual(response.status_code, 403)


    def test_ask(self):
        """An Ask Submission should appear in ask."""
        request = self.factory.post('/submit', {'title': 'Ask: test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.user
        response = submit(request)

        request = self.factory.get('/ask')
        request.user = self.user
        response = index(request)

        submission = Item.objects.get()
        self.assertEqual(submission.is_show, False)
        self.assertEqual(submission.is_ask, True)

        self.assertContains(response, 'test-post-asdf')

    def test_show(self):
        """A Show Submission should appear in show."""
        request = self.factory.post('/submit', {'title': 'Show: test-post-asdf', 'url': 'https://sebastiansteins.com'})
        request.user = self.user
        response = submit(request)

        request = self.factory.get('/show')
        request.user = self.user
        response = index(request)

        submission = Item.objects.get()
        self.assertEqual(submission.is_show, True)
        self.assertEqual(submission.is_ask, False)

        self.assertContains(response, 'test-post-asdf')


    def test_comment(self):
        """A user can comment on a submission."""
        submission = Story(
            user=self.other_user,
            title="Test-1234",
            text="bla"
        )
        submission.save()
        self.assertEqual(Story.objects.get(pk=submission.pk).num_comments, 0)

        request = self.factory.post(submission.get_absolute_url, {'text': 'ACOMMENT'})
        request.user = self.user
        response = item(request, pk=submission.pk)
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(Story.objects.get(pk=submission.pk).num_comments, 1)

        request = self.factory.get('/item/'+str(submission.pk))
        request.user = self.user
        response = item(request, pk=submission.pk)
        self.assertContains(response, "ACOMMENT")

        request = self.factory.get('/comments')
        request.user = self.user
        response = comments(request)
        self.assertContains(response, "ACOMMENT")

    def test_owner_can_edit_comment(self):
        _item = Story(title="Test story", user=self.other_user, text='Bla')
        _item.save()

        comment = Comment(to_story=_item, text='A Comment', user=self.user)
        comment.save()

        self.assertEqual(comment.text, 'A Comment')

        url = '/item/%s/edit'%(comment.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.user
        response = item_edit(request, pk=comment.pk)
        self.assertEqual(response.status_code, 302)

        comment = Comment.objects.get(pk=comment.pk)
        self.assertEqual(comment.text, 'B Comment')


    def test_owner_cannot_edit_comment_with_children(self):
        _item = Story(title="Test story", user=self.other_user, text='Bla')
        _item.save()

        comment = Comment(to_story=_item, text='A Comment', user=self.user)
        comment.save()

        comment2 = Comment(to_story=_item, text='XXXX', user=self.user, parent=comment)
        comment2.save()

        self.assertEqual(comment.text, 'A Comment')

        url = '/item/%s/edit'%(comment.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.user
        response = item_edit(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        comment = Comment.objects.get(pk=comment.pk)
        self.assertEqual(comment.text, 'A Comment')


    def test_owner_can_edit_story(self):
        _item = Story(title="Test story", user=self.user, text='Bla')
        _item.save()

        self.assertEqual(_item.text, 'Bla')

        url = '/item/%s/edit'%(_item.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.user
        response = item_edit(request, pk=_item.pk)
        self.assertEqual(response.status_code, 302)

        _item = Story.objects.get(pk=_item.pk)
        self.assertEqual(_item.text, 'B Comment')


    def test_owner_cannot_edit_story_url(self):
        _item = Story(title="Test story", user=self.user, text='Bla', url="https://test1.example.org")
        _item.save()

        self.assertEqual(_item.text, 'Bla')

        url = '/item/%s/edit'%(_item.pk)
        request = self.factory.post(url, {'url': 'https://example.org'})
        request.user = self.user
        response = item_edit(request, pk=_item.pk)
        self.assertEqual(response.status_code, 302)

        _item = Story.objects.get(pk=_item.pk)
        self.assertEqual(_item.url, 'https://test1.example.org')


    def test_owner_cannot_edit_story_with_comments(self):
        _item = Story(title="Test story", user=self.user, text='Bla')
        _item.save()

        comment = Comment(to_story=_item, text='A Comment', user=self.user)
        comment.save()

        self.assertEqual(_item.text, 'Bla')

        url = '/item/%s/edit'%(_item.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.user
        response = item_edit(request, pk=_item.pk)
        self.assertEqual(response.status_code, 403)

        _item = Story.objects.get(pk=_item.pk)
        self.assertEqual(_item.text, 'Bla')


    def test_other_cannot_edit_comment(self):
        _item = Story(title="Test story", user=self.other_user, text='Bla')
        _item.save()

        comment = Comment(to_story=_item, text='A Comment', user=self.user)
        comment.save()

        self.assertEqual(comment.text, 'A Comment')

        url = '/item/%s/edit'%(comment.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.other_user
        response = item_edit(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        comment = Comment.objects.get(pk=comment.pk)
        self.assertEqual(comment.text, 'A Comment')

    def test_other_cannot_edit_story(self):
        _item = Story(title="Test story", user=self.user, text='Bla')
        _item.save()

        self.assertEqual(_item.text, 'Bla')

        url = '/item/%s/edit'%(_item.pk)
        request = self.factory.post(url, {'text': 'B Comment'})
        request.user = self.other_user
        response = item_edit(request, pk=_item.pk)
        self.assertEqual(response.status_code, 403)

        _item = Story.objects.get(pk=_item.pk)
        self.assertEqual(_item.text, 'Bla')

    def test_owner_can_delete_comment(self):
        story = Story(title='A story', user=self.user, url="https://example.org")
        story.save()

        comment = Comment(to_story=story, user=self.user, text="a comment")
        comment.save()

        url = '/item/%s/delete'%(comment.pk)
        request = self.factory.get(url)
        request.user = self.user
        response = item_delete(request, pk=comment.pk)
        self.assertContains(response, 'sure')

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 1)

        request = self.factory.post(url)
        request.user = self.user
        response = item_delete(request, pk=comment.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, story.get_absolute_url())

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 0)


    def test_owner_cannot_delete_comment_with_children(self):
        story = Story(title='A story', user=self.user, url="https://example.org")
        story.save()

        comment = Comment(to_story=story, user=self.user, text="a comment")
        comment.save()

        comment2 = Comment(to_story=story, user=self.user, text="another comment", parent=comment)
        comment2.save()

        url = '/item/%s/delete'%(comment.pk)
        request = self.factory.get(url)
        request.user = self.user
        response = item_delete(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 1)

        request = self.factory.post(url)
        request.user = self.user
        response = item_delete(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 1)


    def test_owner_can_delete_story(self):
        story = Story(title='A story', user=self.user, url="https://example.org")
        story.save()


        url = '/item/%s/delete'%(story.pk)
        request = self.factory.get(url)
        request.user = self.user
        response = item_delete(request, pk=story.pk)
        self.assertContains(response, 'sure')

        self.assertEqual(Story.objects.filter(pk=story.pk).count(), 1)

        request = self.factory.post(url)
        request.user = self.user
        response = item_delete(request, pk=story.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        self.assertEqual(Story.objects.filter(pk=story.pk).count(), 0)


    def test_other_cannot_delete_comment(self):
        story = Story(title='A story', user=self.user, url="https://example.org")
        story.save()

        comment = Comment(to_story=story, user=self.user, text="a comment")
        comment.save()

        url = '/item/%s/delete'%(comment.pk)
        request = self.factory.get(url)
        request.user = self.other_user
        response = item_delete(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 1)

        request = self.factory.post(url)
        request.user = self.other_user
        response = item_delete(request, pk=comment.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Comment.objects.filter(pk=comment.pk).count(), 1)


    def test_other_cannot_delete_story(self):
        story = Story(title='A story', user=self.user, url="https://example.org")
        story.save()

        url = '/item/%s/delete'%(story.pk)
        request = self.factory.get(url)
        request.user = self.other_user
        response = item_delete(request, pk=story.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Story.objects.filter(pk=story.pk).count(), 1)

        request = self.factory.post(url)
        request.user = self.other_user
        response = item_delete(request, pk=story.pk)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Story.objects.filter(pk=story.pk).count(), 1)


    def test_zen(self):
        s = 'The Zen of'
        url = '/zen'
        request = self.factory.get(url)
        request.user = self.user
        response = zen(request)
        self.assertContains(response, s)


    def test_comments(self):
        url = '/comments'
        request = self.factory.get(url)
        request.user = self.user
        response = comments(request)
        self.assertEqual(response.status_code, 200)

    def test_threads(self):
        url = '/threads'
        request = self.factory.get(url)
        request.user = self.user
        response = threads(request)
        self.assertEqual(response.status_code, 200)

    def test_newest(self):
        url = '/newest'
        request = self.factory.get(url)
        request.user = self.user
        response = newest(request)
        self.assertEqual(response.status_code, 200)

    def test_front_page(self):
        url = '/'
        request = self.factory.get(url)
        request.user = self.user
        response = index(request)
        self.assertEqual(response.status_code, 200)

    def test_more_button(self):
        self.fail() # TODO


class ReceiversNewsTest(TestCase):
    """Tests the basic functionality of the news app."""
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='sebst', email='hi@seb.st', password='top_secret')
        self.other_user = CustomUser.objects.create_user(
            username='bla1', email='two@seb.st', password='top_secret')


    def test_mark_show_and_ask(self):
        story = Story(title="Ask: Some ask story", text="..", user=self.user)
        self.assertEqual(story.is_ask, False)
        story.save()
        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.is_ask, True)

        story = Story(title="Show: Some show story", text="..", user=self.user)
        self.assertEqual(story.is_show, False)
        story.save()
        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.is_show, True)


    def test_create_self_upvote_for_submission(self):
        story = Story(title="Some story", text="..", user=self.user)
        self.assertEqual(Vote.objects.filter(item=story).count(), 0)
        story.save()
        self.assertEqual(Vote.objects.filter(item=story).count(), 1)


    def test_check_for_duplicates(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        story2 = Story(title="Once again", url="http://example.org", user=self.other_user)
        story2.save()

        story = Story.objects.get(pk=story.pk)
        story2 = Story.objects.get(pk=story2.pk)
        self.assertEqual(story.duplicate_of, None)
        # Duplicate story needs to be marked as duplicate
        self.assertEqual(story2.duplicate_of, story)
        # Second submission triggers upvote on original story
        self.assertEqual(Vote.objects.filter(item=story).count(), 2)


    def test_update_votes_count_on_submission(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        self.assertEqual(Vote.objects.filter(item=story).count(), 1)

        vote = Vote(user=self.user, vote=1, item=story)
        vote.save()
        story = Story.objects.get(pk=story.pk)

        self.assertEqual(story.upvotes, 1)
        self.assertEqual(story.points, 1)
        self.assertEqual(story.downvotes, 0)

        vote2 = Vote(user=self.other_user, vote=-1, item=story)
        vote2.save()
        story = Story.objects.get(pk=story.pk)

        self.assertEqual(story.upvotes, 1)
        self.assertEqual(story.points, 0)
        self.assertEqual(story.downvotes, 1)



    def test_update_user_karma_on_vote(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        user = CustomUser.objects.get(pk=self.user.pk)
        self.assertEqual(user.karma, 0)

        vote2 = Vote(user=self.other_user, vote=1, item=story)
        vote2.save()
        story = Story.objects.get(pk=story.pk)
        user = CustomUser.objects.get(pk=self.user.pk)

        self.assertEqual(user.karma, 1)


    def test_update_comments_count_on_submission(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 0)

        comment1 = Comment(to_story=story, text="...", user=self.other_user)
        comment1.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 1)

        comment2 = Comment(to_story=story, text="...", user=self.user, parent=comment1)
        comment2.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 2)


    def test_update_comments_count_on_deletion(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 0)

        comment1 = Comment(to_story=story, text="...", user=self.other_user)
        comment1.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 1)

        comment2 = Comment(to_story=story, text="...", user=self.user, parent=comment1)
        comment2.save()

        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 2)

        comment1.delete()
        story = Story.objects.get(pk=story.pk)
        self.assertEqual(story.num_comments, 0)


    def test_update_item_votes_on_unvote(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        self.assertEqual(Vote.objects.filter(item=story).count(), 1)

        vote = Vote(user=self.user, vote=1, item=story)
        vote.save()
        story = Story.objects.get(pk=story.pk)

        self.assertEqual(story.upvotes, 1)
        self.assertEqual(story.points, 1)
        self.assertEqual(story.downvotes, 0)

        vote2 = Vote(user=self.other_user, vote=-1, item=story)
        vote2.save()
        story = Story.objects.get(pk=story.pk)

        self.assertEqual(story.upvotes, 1)
        self.assertEqual(story.points, 0)
        self.assertEqual(story.downvotes, 1)

        vote2.delete()

        story = Story.objects.get(pk=story.pk)

        self.assertEqual(story.upvotes, 1)
        self.assertEqual(story.points, 1)
        self.assertEqual(story.downvotes, 0)


    def test_update_user_karma_on_unvote(self):
        story = Story(title="Some story", url="http://example.org", user=self.user)
        story.save()

        user = CustomUser.objects.get(pk=self.user.pk)
        self.assertEqual(user.karma, 0)

        vote2 = Vote(user=self.other_user, vote=1, item=story)
        vote2.save()
        story = Story.objects.get(pk=story.pk)

        user = CustomUser.objects.get(pk=self.user.pk)
        self.assertEqual(user.karma, 1)

        vote2.delete()
        user = CustomUser.objects.get(pk=self.user.pk)
        self.assertEqual(user.karma, 0)


    def test_add_domain_to_link_stories(self):
        item = Story('title': 'bla', url='https://Example.org', user=self.user)
        item.save()

        item = Story.objects.get(pk=item.pk)
        self.assertEqual(item.domain, 'example.org')