import base64

from ..models.follower import Follow
from ..models import Node
from django.contrib.auth import authenticate


def validateAuthorDict(authorDict):
    """
    Validate the author dictionary. Returns True if the author dictionary is valid, False otherwise.
    """

    if not authorDict:
        return False
    if not authorDict.get('id'):
        return False
    if not authorDict.get('displayName'):
        return False
    if not authorDict.get('url'):
        return False
    if not authorDict.get('host'):
        return False
    return True


def validateNode(hostURL, auth_header):
    """
    Given a host URL, validate that the host is a url to a node and the username and password is correct.
    hostURL: The host URL of the client making the request to this server.
    auth_header: The Authorization header of the request. Used to retrieve the username and password.
    Returns the node object if the host is a node, None otherwise.
    """
    try:
        node = Node.objects.get(url__contains=hostURL)

        # Get username and password from auth header, then authenticate with the username and password
        # Source code from https://stackoverflow.com/a/38044377
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(
            encoded_credentials).decode("utf-8").split(':')
        username = decoded_credentials[0]
        password = decoded_credentials[1]

        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return None

    except Node.DoesNotExist:
        return None

    return node


def validateFriends(author1, author2):
    """
    Given two authors, validate that they are friends. Returns True if they are friends, False otherwise.
    """

    author1_follows_author2 = Follow.objects.filter(
        follower=author1, followed=author2, pending=False).exists()
    author2_follows_author1 = Follow.objects.filter(
        follower=author2, followed=author1, pending=False).exists()

    return author1_follows_author2 and author2_follows_author1
