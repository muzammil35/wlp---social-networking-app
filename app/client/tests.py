from django.test import TestCase
from django.urls import reverse
from api.models import Post, Author, Comment
from django.contrib.auth.models import User

class CommentViewTests(TestCase):
    def setUp(self):
        # Setup a user, author, and a post for testing
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.author = Author.objects.create(user=self.user, displayName="Test Author")
        self.post = Post.objects.create(title="Test Post", content="Test Content", author=self.author)
        self.client.login(username='testuser', password='12345')

    def test_comment_form_not_displayed_by_default(self):
        response = self.client.get(reverse('client:post_detail', kwargs={'post_id': self.post.id}))
        self.assertNotContains(response, 'id="commentFormContainer"')

    def test_comment_form_displayed_with_query_parameter(self):
        response = self.client.get(reverse('client:post_detail', kwargs={'post_id': self.post.id}) + '?add_comment=true')
        self.assertContains(response, 'id="commentFormContainer"')

    def test_submit_comment(self):
        comment_count_before = Comment.objects.count()
        response = self.client.post(reverse('client:submit_comment', kwargs={'post_id': self.post.id}) + '?add_comment=true', {'comment': 'A test comment', 'contentType': 'text/plain'})
        comment_count_after = Comment.objects.count()
        self.assertEqual(comment_count_after, comment_count_before + 1)

    def test_submit_comment_without_form(self):
        # This test assumes that your view logic prevents comment submission if the form isn't supposed to be displayed
        comment_count_before = Comment.objects.count()
        response = self.client.post(reverse('client:post_detail', kwargs={'post_id': self.post.id}), {'comment': 'Another test comment', 'contentType': 'text/plain'})
        comment_count_after = Comment.objects.count()
        # Assuming your view correctly handles this, the count shouldn't change
        self.assertEqual(comment_count_after, comment_count_before)
