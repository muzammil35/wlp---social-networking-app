from ast import parse
from cmath import e
from urllib.parse import urlparse
import requests
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token

from ..models.inboxEntry import InboxEntry

from ..models.node import Node


def postToInbox(inboxURL, data, request):
    """
    Helper function to post a message to the inbox of a user. 
    If inbox is remote, check whether url is registered as a node and send the message to the inbox of the remote user.
    """
    if not inboxURL:
        return

    # Check whether the inbox is local or remote
    parsed_uri = urlparse(inboxURL)
    host = parsed_uri.netloc

    try:
        if request.get_host() == host:
            # Inbox is local
            inboxAuthorId = parsed_uri.path.split('/')[4]

            newInboxEntry = InboxEntry.objects.create(
                entry_json=data, author_id=inboxAuthorId)

        else:
            node = get_object_or_404(Node, url__contains=host)
            # set ''Access-Control-Allow-Origin' header to allow cross-origin requests
            response = requests.post(
                inboxURL, json=data, auth=(node.username, node.password), headers={'Access-Control-Allow-Origin': '*', 'referer': request.build_absolute_uri('/')}, timeout=3)
            print("Response from remote inbox",
                  response.status_code, response.text)
    except requests.exceptions.RequestException as e:
        print("Error", e)
        print("Read timeout error posting to inbox.", inboxURL, data)
    except Exception as e:
        print("Error posting to inbox.", inboxURL, data)
        print("Error:", e)
