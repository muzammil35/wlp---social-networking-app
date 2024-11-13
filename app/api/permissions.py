import base64
from email import message
from email.mime import audio
from rest_framework import permissions
from urllib.parse import urlparse

from .models.node import Node
from .utils.validation import validateNode
from django.contrib.auth import authenticate


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Based from DRF's authentication tutorial at: https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/#object-level-permissions
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.

        # If the object has an author attribute, that means obj is a Post/Comment/Like object
        if hasattr(obj, 'author'):
            return obj.author.user.id == request.user.id
        return obj.user == request.user


class NodePermission(permissions.BasePermission):
    message = 'You are requesting from a node that is not allowed.'

    def has_permission(self, request, view):
        referer = request.META.get('HTTP_REFERER')
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        print("REFERRER: ", referer)
        print("ABSOLUTE URI: ", request.build_absolute_uri('/'))

        if referer is None:
            if auth_header:
                # Get username and password from auth header, then authenticate with the username and password
                # Source code from https://stackoverflow.com/a/38044377
                encoded_credentials = auth_header.split(' ')[1]
                decoded_credentials = base64.b64decode(
                    encoded_credentials).decode("utf-8").split(':')
                username = decoded_credentials[0]
                password = decoded_credentials[1]

                user = authenticate(username=username, password=password)
                if user is None or not user.is_active:
                    print("Can't authenticate with the given credentials")
                    return False

                try:
                    node = Node.objects.get(user=user)
                    return True
                except Node.DoesNotExist:
                    print("Can't find a node with that credentials")
                    return False
            else:
                print("No auth headers provided.")
                return False

        parsed_uri = urlparse(referer)
        refererHost = parsed_uri.netloc

        # If the originating host is the same as the host of the server, then the request is valid
        if refererHost in request.build_absolute_uri('/'):
            return True

        node = validateNode(refererHost, auth_header)

        if node is None:
            return False

        return True
