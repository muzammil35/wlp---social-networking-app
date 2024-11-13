from django.db import models
from django.conf import settings
import uuid

from .author import Author


class InboxEntry(models.Model):
    """
    Represent an inbox entry for an author. 
    """
    class EntryType(models.TextChoices):
        POST = 'post'
        COMMENT = 'comment'
        follow = 'follow'
        LIKE = 'like'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # The author that inbox entry is for
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE)
    createdAt = models.DateTimeField(auto_now_add=True)
    entry_json = models.JSONField()
    seen = models.BooleanField(default=False) #this is for the notification badges

    """
    Entry JSON is a JSON object that could be of type (see their respective serializers for more details):
    1. author
    2. post
    3. comment
    4. like
    5. follow
    """
