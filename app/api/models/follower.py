from django.db import models
from django.conf import settings
import uuid

from .author import Author


class Follow(models.Model):
    """
    Represent the following relationship between two authors.
    """
    class Meta:
        unique_together = ('followed', 'follower')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pending = models.BooleanField(default=True)

    # The author that is followed by author in "following" field
    followed = models.ForeignKey(
        Author, related_name='followed', on_delete=models.CASCADE)

    # The author that follows the author in "following" field
    follower = models.ForeignKey(
        Author, related_name='follower', on_delete=models.CASCADE)
