from hmac import new
import uuid
from datetime import datetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
import requests
from ..models.follower import Follow
from ..models.node import Node
from ..utils.validation import validateAuthorDict
from ..docs.inboxSchema import INBOX_ENTRY_ADD_REQUEST_BODY
from ..serializers.postSerializer import LikeSerializer, PostSerializer, CommentSerializer
from ..serializers.inboxSerializer import InboxEntrySerializer
from ..models import Author, Post, Like, InboxEntry, Comment
from django.http import Http404


class NotificationListView(APIView):
    swagger_schema = None
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id, format=None):
        """
        Get all notifications for a specific author, which consists of:
        1. Likes
        2. Comments
        3. Posts shared

        Does not include follow requests.
        """

        try:
            author = Author.objects.get(user=request.user.id)
        except Author.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Must be logged in to view inbox.'})

        # Check that the author_id is the same as the authenticated user
        if (author_id != author.id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You can only view your own inbox.'})

        inboxEntries = InboxEntry.objects.filter(
            author=author_id).order_by('-createdAt')
        inboxEntries.update(seen=True)
        inboxEntries = inboxEntries.values()
        inboxEntriesContents = []

        for entry in inboxEntries:
            if entry['entry_json'].get('type') == 'follow':
                continue

            inboxEntriesContents.append(entry['entry_json'])

        return Response({"items": inboxEntriesContents, "type": "inbox"}, status=status.HTTP_200_OK)


class InboxDetail(APIView):

    @swagger_auto_schema(responses={200: InboxEntrySerializer()}, tags=['Inbox'])
    def get(self, request, author_id, format=None):
        """Get the inbox for a specific author."""
        try:
            author = Author.objects.get(user=request.user.id)
        except Author.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Must be logged in to view inbox.'})

        # Check that the author_id is the same as the authenticated user
        if (author_id != author.id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You can only view your own inbox.'})

        inboxEntries = InboxEntry.objects.filter(
            author=author_id).order_by('-createdAt')
        inboxEntries = inboxEntries.values()
        inboxEntriesContents = []

        for entry in inboxEntries:
            entryJson = entry['entry_json']

            # Check if the post exists in the db.
            if entryJson.get('type') == 'post' and Post.objects.filter(pk=entryJson.get('id').split('/')[-1]).exists():
                inboxEntriesContents.append(entry['entry_json'])

        return Response({"items": inboxEntriesContents, "type": "inbox"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=INBOX_ENTRY_ADD_REQUEST_BODY, responses={201: InboxEntrySerializer}, tags=['Inbox'])
    def post(self, request, author_id, format=None):
        """
        Add a new entry to the inbox for a specific author. 
        The request body should be one of object type: post, Like, comment, follow 
        """
        # The author that the inbox belongs to
        inboxAuthor = get_object_or_404(Author, pk=author_id)

        entry_type = request.data.get('type')

        entry_type = entry_type.lower()

        print("Received inbox entry", request.data)

        if entry_type not in [c[0] for c in InboxEntry.EntryType.choices]:
            return Response({"error": f"Entry type {entry_type} not recognized"}, status=status.HTTP_400_BAD_REQUEST)

        if entry_type == 'like':
            return addLikeToInbox(inboxAuthor, request)
        elif entry_type == 'comment':
            return addCommentToInbox(inboxAuthor, request)
        elif entry_type == 'follow':
            return addFollowToInbox(inboxAuthor, request)
        elif entry_type == 'post':
            return addPostToInbox(inboxAuthor, request)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, author_id, format=None):
        """
        Delete all entries in the inbox for a specific author.
        """
        try:
            author = Author.objects.get(user=request.user.id)
        except Author.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Must be logged in to clear inbox.'})

        # Check that the author_id is the same as the authenticated user
        if (author_id != author.id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You can only clear your own inbox.'})

        inboxEntries = InboxEntry.objects.filter(
            author=author_id).order_by('-createdAt')
        inboxEntries.delete()

        return Response(status=status.HTTP_204_NO_CONTENT, data={'message': 'Inbox cleared.'})


def addLikeToInbox(inboxAuthor: Author, request):
    """
    When a like is added to inbox, check that the like object does not exist in the db yet. 
    So we need to create the like object and then add it to the inbox.
    """

    objectURL = request.data.get('object')
    if objectURL is None:
        return Response({"error": "object is required"}, status=status.HTTP_400_BAD_REQUEST)

    post_id = objectURL.split('/')[-1]

    # The author liking the post
    author = request.data.get('author')

    if author is None:
        return Response({"error": "author is required"}, status=status.HTTP_400_BAD_REQUEST)

    authorURL = author.get('url')

    try:
        likeAuthor = Author.objects.get(url__contains=authorURL)
    except Author.DoesNotExist:
        # If the author doesn't exist, it means the like is from a remote server.
        # Create a copy of the author and add it to the db, with a user object that is not active.
        likeAuthor = createForeignAuthor(author)
        if likeAuthor is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid author json.'})

    post = get_object_or_404(Post, pk=post_id)

    try:
        like = Like.objects.create(author=likeAuthor, post=post)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Like already exists.'})

    likeSerializer = LikeSerializer(like, context={'request': request})
    newInboxEntry = InboxEntry.objects.create(
        author=inboxAuthor, entry_json=request.data)
    entrySerializer = InboxEntrySerializer(
        newInboxEntry)

    return Response(entrySerializer.data, status=status.HTTP_201_CREATED)


def addCommentToInbox(inboxAuthor, request):

    comment_id = request.data.get('id').split('/')[-1]
    author = request.data.get('author')
    post_id = request.data.get('id').split('/')[-3]

    if author is None:
        return Response({"error": "author is required"}, status=status.HTTP_400_BAD_REQUEST)

    authorURL = author.get('url')

    post = get_object_or_404(Post, pk=post_id)

    try:
        # Check whether comment id is valid uuid. Context: Some groups don't use uuid as id
        try:
            uuid.UUID(comment_id).version
        except ValueError:
            comment_id = uuid.uuid4()

        commentAuthor = Author.objects.get(url__contains=authorURL)
    except Author.DoesNotExist:
        # If the author doesn't exist, it means the comment is from a remote server.
        # Create a copy of the author and add it to the db, with a user object that is not active.
        commentAuthor = createForeignAuthor(author)
        if commentAuthor is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid author json.'})

    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        comment_data = {
            'post': post,
            'author': commentAuthor,
            'comment': request.data.get('comment'),
            'published': datetime.fromisoformat(request.data.get('published'))
        }
        # Comment came from remote Author so not yet created in our DB
        comment = Comment.objects.create(**comment_data)
        # save new comment to DB
        comment.save()

        post.count += 1
        post.save()

    commentSerializer = CommentSerializer(
        comment, context={'request': request})
    newInboxEntry = InboxEntry.objects.create(
        author=inboxAuthor, entry_json=request.data)
    entrySerializer = InboxEntrySerializer(
        newInboxEntry)

    return Response(entrySerializer.data, status=status.HTTP_201_CREATED)


def addFollowToInbox(inboxAuthor, request):
    """
    When a follow is added to inbox, the person receiving this follow request 
    have the option to accept or reject the follow request (in the frontend).

    If accepted, then call PUT to /authors/{AUTHOR_ID}/followers/{FOREIGN_AUTHOR_ID} endpoint.
    If rejected, do nothing.
    """
    localAuthor = request.data.get('object')
    authorType = localAuthor.get('type').lower()
    if authorType != 'author':
        return Response({"error": "object must be of type author"}, status=status.HTTP_400_BAD_REQUEST)

    # Check that the author exists in the db
    try:
        localAuthorId = localAuthor.get('url')
        localAuthorId = localAuthorId.split('/')[-2]
        localAuthor = Author.objects.get(pk=localAuthorId)
    except Author.DoesNotExist:
        return Response({"error": "author you're trying to follow does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    actor = request.data.get('actor')
    actorType = actor.get('type').lower()
    if actorType != 'author':
        return Response({"error": "actor must be of type author"}, status=status.HTTP_400_BAD_REQUEST)

    # Check that the actor exists in the db, if not create a new author object
    try:
        actorURL = actor.get('url')
        actor = Author.objects.get(url__contains=actorURL)
    except Author.DoesNotExist:
        actor = createForeignAuthor(actor)
        if actor is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid actor json.'})

    try:
        follow = Follow.objects.create(follower=actor, followed=localAuthor)
    except:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Follow already exists.'})

    newInboxEntry = InboxEntry.objects.create(
        author=inboxAuthor, entry_json=request.data)
    entrySerializer = InboxEntrySerializer(newInboxEntry)

    return Response(entrySerializer.data, status=status.HTTP_201_CREATED)


def addPostToInbox(inboxAuthor: Author, request):
    """
    When a post is added to inbox, the post may or may not exist in this server. 
    If it exist, then it's a local post. If it doesn't exist, then it's a post from remote server.
    """
    post_origin = request.data.get('origin')

    if post_origin is None:
        return Response({"error": "origin is required"}, status=status.HTTP_400_BAD_REQUEST)

    # The author the post
    author = request.data.get('author')

    if author is None:
        return Response({"error": "author is required"}, status=status.HTTP_400_BAD_REQUEST)

    # If the author doesn't exist, it means the like is from a remote server.
    # Create a copy of the author and add it to the db, with a user object that is not active.
    try:
        authorURL = author.get('url')
        postAuthor = Author.objects.get(url__contains=authorURL)
    except Author.DoesNotExist:
        postAuthor = createForeignAuthor(author)
        if postAuthor is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid author json.'})

    # If the post doesn't exist, it means the post is from a remote server.
    # Create a copy of the post and add it to the db.
    try:
        post = Post.objects.get(origin=post_origin)

        postSerializer = PostSerializer(post, context={'request': request})
    except Post.DoesNotExist:
        newPostId = str(uuid.uuid4())
        newPostSource = request.build_absolute_uri(
            'api/v1/authors/' + str(postAuthor.id) + '/posts/' + newPostId)

        newPost = Post.objects.create(
            id=newPostId, author=postAuthor, origin=post_origin, description=request.data.get(
                'description'),
            contentType=request.data.get('contentType'), content=request.data.get('content', ''),
            published=request.data.get('published'), visibility=request.data.get('visibility'),
            title=request.data.get('title'), source=newPostSource, count=request.data.get('count', 0)
        )
        postSerializer = PostSerializer(newPost, context={'request': request})

        # Grab first page of comments and add them to db
        commentSrc = request.data.get('commentsSrc')
        if commentSrc:
            comments = comments.get('comments', [])

            for comment in comments:
                # Check whether comment author exists in db
                commentAuthorJson = comment.get('author')
                if commentAuthor is None:
                    continue

                try:
                    commentAuthor = Author.objects.get(
                        url__contains=commentAuthorJson.get('url'))
                except Author.DoesNotExist:
                    commentAuthor = createForeignAuthor(commentAuthorJson)

                Comment.objects.create(
                    post=newPostId,
                    author=commentAuthor,
                    comment=comment.get('comment', ''),
                )

    newInboxEntry = InboxEntry.objects.create(
        author=inboxAuthor, entry_json=postSerializer.data)
    entrySerializer = InboxEntrySerializer(
        newInboxEntry)

    return Response(entrySerializer.data, status=status.HTTP_201_CREATED)


def createForeignAuthor(authorDict, useUrlAsId=False):
    """
    Given a author dictionary, create a new author object and return it. 
    If the author dictionary is invalid, return None.
    """
    if not validateAuthorDict(authorDict):
        print("invalid author dict")
        return None

    # Check whether author is from are-http
    isAreHttp = False
    if 'are-you-http' in authorDict.get('host'):
        isAreHttp = True

    authorURL = authorDict.get('url')
    if authorURL[-1] != '/':
        authorURL += '/'

    github = authorDict.get('github')
    if github is None:
        github = " "

    newAuthorId = authorDict.get('id', '').split(
        '/')[-1] if isAreHttp else uuid.uuid4()

    print("Creating new foreign author: ",
          newAuthorId, authorDict['displayName'], authorURL)

    newAuthor = Author.objects.create(
        user=None, displayName=authorDict['displayName'], approved=False,
        host=authorDict['host'], url=authorURL, profile_image=authorDict.get(
            'profileImage', " "),
        github=github,
        id=newAuthorId
    )
    print("newAuthor created")
    return newAuthor

class CheckNewNotifications(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, author_id, format=None):
        # Ensure the author_id in the URL matches the logged-in user's author ID
        author = get_object_or_404(Author, id=author_id)

        # Security Check: Ensure the logged-in user is the author they claim to be
        if not request.user.author.id == author.id:
            return Response({"error": "Unauthorized"}, status=403)

        unseen_count = InboxEntry.objects.filter(author=author_id, seen=False).count()

        # Return a JSON response indicating whether there are unseen notifications
        return Response({"has_new": unseen_count > 0, "unseen_count": unseen_count})