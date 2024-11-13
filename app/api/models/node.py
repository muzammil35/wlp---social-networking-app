from django.db import models
from django.conf import settings
import uuid


class Node(models.Model):
    """
    Represent another team's client. 
    Server admin would create a user to associate the node with. 
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # The user that this node is associated with. To allow nodes to connect to this server,
    # we would create a user for them and give them the username and password.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nodes')

    # Username and password for server to connect to the node with Basic Auth.
    # For other nodes to connect to this server, we would create a user for them.
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    

    # URL of the node including prefix, example: /api/v1/
    url = models.URLField()
