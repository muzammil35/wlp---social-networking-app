from drf_yasg import openapi

from ..models.inboxEntry import InboxEntry

INBOX_ENTRY_ADD_REQUEST_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT)
