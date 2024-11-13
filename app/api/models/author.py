from django.db import models
from django.conf import settings
import uuid


class Author(models.Model):
    # For foreign authors, the id may not be the same as the id in their server. URL field is used to store the id in their server.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    displayName = models.CharField(max_length=60)
    approved = models.BooleanField(default=False)
    github = models.CharField(max_length=200, blank=True, null=True)

    host = models.URLField(max_length=200)
    # URL to the author's profile. If the author is foreign, the URL will be the URL of the author's server.
    url = models.URLField(max_length=400)

    # Link to the profile image
    profile_image = models.CharField(max_length=200, blank=True, null=True)
