import base64
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404

from ..models import Post, Author, Like, Comment


def create_test_user_and_author():
    user = User.objects.create_user('john', 'john@example.com', 'johnpassword')
    author = Author.objects.create(
        user=user,
        displayName="JohnDoe",
        approved=True,
        github="https://github.com/johndoe",
        profile_image="url/to/image"
    )

    return user, author


class PostCreationTests(TestCase):
    def setUp(self):
        self.user, self.author = create_test_user_and_author()
        self.original_post = Post.objects.create(
            title="Original Post",
            source="http://source.url",
            origin="http://origin.url",
            description="This is a test post",
            author=self.author,
            content="Original content",
            contentType='text/plain',
            visibility=Post.Visibility.PUBLIC,
            published=timezone.now(),
        )

        credentials = base64.b64encode(b'john:johnpassword').decode('ascii')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials

    def test_create_post(self):
        self.client.login(username='john', password='johnpassword')
        response = self.client.post(reverse('api:post_list', kwargs={'author_id': self.author.id}), data={
            'title': 'Test Post',
            'content': 'This is a test post.',
            'description': 'Test description.',
            'visibility': 'PUBLIC',
            'contentType': 'text/plain',
        })
        # Using 201 as an example for successful creation
        self.assertEqual(response.status_code, 201, msg=response.content)
        # Assuming one post was already created in setUp
        self.assertEqual(Post.objects.count(), 2)


# TODO: Implement share test once share functionality is implemented
# class PostSharingTests(TestCase):
#     def setUp(self):
#         self.user, self.author = create_test_user_and_author()
#         self.post = Post.objects.create(
#             author=self.author,
#             title="Original Post",
#             content="Original content",
#             visibility=Post.Visibility.PUBLIC,
#             contentType='text/plain',
#             published=timezone.now(),
#         )

#     def test_share_post(self):
#         self.client.login(username='john', password='johnpassword')
#         response = self.client.post(reverse('api:share_post', kwargs={'author_id': self.author.id, 'post_id': self.post.id}),
#                                     {'title': 'Test Post', 'content': 'This is a test post.', 'description': 'Test description.'})
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Post.objects.count(), 2)


class PostLikeTests(TestCase):
    def setUp(self):
        self.user, self.author = create_test_user_and_author()
        self.post = Post.objects.create(
            title="Test Post",
            source="http://source.url",
            origin="http://origin.url",
            description="A test post for liking functionality.",
            author=self.author,
            content="Test content",
            contentType='text/plain',
            visibility=Post.Visibility.PUBLIC,
            published=timezone.now(),
        )

    def test_like_count(self):
        # First, create a like for the post
        Like.objects.create(post=self.post, author=self.author)

        self.post.save()

        # Perform the unlike action
        self.client.login(username='john', password='johnpassword')
        response = self.client.get(
            reverse('api:post_like_list', kwargs={'author_id': self.author.id, 'post_id': self.post.id}))

        # Refresh to get the updated like_count
        self.post.refresh_from_db()

        # Parse the JSON response - FOR MAX
        # likes_list = response.json()

        # Assuming the likes are returned as a list under a key, for example, "likes" ....
        # likes_count = len(likes_list)
        # self.assertEqual(likes_count, 1)
        # Like.objects.delete(post=self.post, author = self.author) - USELESS?!

        # Assuming a redirect happens after unliking
        # self.assertEqual(response.status_code, 200)
        # Like count should decrement to 0
        # self.assertEqual(likes_count, 0)


class PostDeletionTests(TestCase):
    def setUp(self):
        self.user, self.author = create_test_user_and_author()

        # Create a post by the author
        self.post = Post.objects.create(
            title="Test Post for Deletion",
            source="http://example.com/source",
            origin="http://example.com/origin",
            description="This post is to be deleted.",
            author=self.author,
            content="Content of the post to be deleted.",
            contentType='text/plain',
            visibility=Post.Visibility.PUBLIC,
            published=timezone.now(),
        )

        credentials = base64.b64encode(b'john:johnpassword').decode('ascii')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials

    def test_delete_post(self):
        self.client.login(username='john', password='johnpassword')

        # Ensure the post exists before deletion attempt
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

        # Perform the delete operation
        response = self.client.delete(
            reverse('api:post_detail', kwargs={'author_id': self.author.id, 'post_id': self.post.id}))

        # Verify that the post has been deleted
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())


class PostEditTests(TestCase):
    def setUp(self):
        # Create a user and a post
        self.user, self.author = create_test_user_and_author()
        self.post = Post.objects.create(
            title="Test Post for Edit",
            source="http://example.com/source",
            origin="http://example.com/origin",
            description="This post is to be edited.",
            author=self.author,
            content="Content of the post to be edited.",
            contentType='text/plain',
            visibility=Post.Visibility.PUBLIC,
            published=timezone.now(),
        )
        self.edit_url = reverse('api:post_detail', kwargs={
                                'author_id': self.author.id, 'post_id': self.post.id})

        credentials = base64.b64encode(b'john:johnpassword').decode('ascii')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials

    def get_object(self, queryset=None):
        post_id = self.kwargs.get("post_id")
        return get_object_or_404(Post, id=post_id)

    def test_edit_form_display(self):
        # Test that the edit form displays with the post's current information
        self.client.login(username='john', password='johnpassword')
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post for Edit')
        self.assertContains(response, 'Content of the post to be edited.')

    def test_successful_edit(self):
        # Test successful edit
        self.client.login(username='john', password='johnpassword')

        self.client.put(
            self.edit_url, data={
                "description": "string",
                "contentType": "text/plain",
                "content": "New content.",
                "visibility": "PUBLIC",
                "title": "New Title"
            }, content_type='application/json')
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'New Title')
        self.assertEqual(self.post.content, 'New content.')


class CommentTests(TestCase):
    def setUp(self):
        self.user, self.author = create_test_user_and_author()
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post content.",
            description="Test description.",
            author=self.author,
            visibility=Post.Visibility.PUBLIC,
            published=timezone.now(),
        )

        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            comment="Test Comment bro",
            published=timezone.now()
        )

    def test_create_comment(self):
        self.client.login(username='john', password='johnpassword')
        response = self.client.post(reverse('api:comment-list', kwargs={'author_id': self.author.id, 'post_id': self.post.id}), {
            'post': str(self.post.id),
            'author': str(self.author.id),
            'comment': "Test Comment bro",
            'published': timezone.now()
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.count(), 2)

    def test_delete_comment(self):
        self.client.login(username='john', password='johnpassword')
        response = self.client.delete(reverse('api:comment-detail', kwargs={
                                      'author_id': self.author.id, 'post_id': self.post.id, 'comment_id': self.comment.id}))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
