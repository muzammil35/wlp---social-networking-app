from django.db import models
from .author import Author
from django.contrib import admin
from django.utils.html import format_html
import uuid


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC"
        FRIENDS = "FRIENDS"
        UNLISTED = "UNLISTED"

    class ContentType(models.TextChoices):
        TEXT = "text/plain"
        MARKDOWN = "text/markdown"
        PNG = "image/png;base64"
        JPEG = "image/jpeg;base64"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    # where did you get this post from?
    source = models.URLField(blank=True, max_length=400)
    # where is it actually from?
    origin = models.URLField(blank=True, max_length=400)
    description = models.TextField()
    author = models.ForeignKey(
        Author, related_name='posts', on_delete=models.CASCADE, default='')  # has access to its Author
    published = models.DateTimeField(auto_now_add=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices)
    contentType = models.CharField(max_length=255, choices=ContentType.choices)
    content = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    count = models.IntegerField(default=0)
    image = models.BinaryField(null=True, blank=True)

    @admin.display
    def preview_image(self):
        if not self.image:
            return None

        from base64 import b64encode
        return format_html('<img src="data:{},{}" width="100" height="100" />', self.contentType, b64encode(self.image).decode('utf8'))


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE)  # author of the comment
    comment = models.TextField(max_length=255)  # comment
    published = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    class Meta:
        unique_together = ('post', 'author')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
