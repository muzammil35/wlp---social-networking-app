from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions

from ..docs.paginationSchema import PAGE_PARAMETER, SIZE_PARAMETER
from ..utils.CustomPagination import CustomPagination
from ..utils.postToInbox import postToInbox
from ..utils.validation import validateFriends
from ..models.follower import Follow
from ..serializers.postSerializer import CommentsSerializer, LikeSerializer, PostSerializer, PostsSerializer, LikesSerializer, CommentSerializer
from ..models import Author, Post, Like, Comment, InboxEntry
from ..permissions import IsOwnerOrReadOnly
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser


class LocalPublicPostList(APIView):
    swagger_schema = None

    @swagger_auto_schema(responses={200: PostsSerializer()}, security=[], tags=['Posts'])
    def get(self, request, format=None):
        """
        List all public posts from local authors.
        """

        posts = Post.objects.filter(
            visibility=Post.Visibility.PUBLIC).order_by('-published')
        serializer = PostsSerializer(
            posts, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostList(APIView, CustomPagination):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(responses={200: PostsSerializer()}, security=[], tags=['Posts'], manual_parameters=[PAGE_PARAMETER, SIZE_PARAMETER])
    def get(self, request, author_id, format=None):
        """List all posts by an author."""

        """
        TODO: Add authentication logic, currently all posts are returned regardless of visibility and permission.
        Not authenticated: only public posts.
        Authenticated locally as author: all posts.
        Authenticated locally as friend of author: public + friends-only posts.
        Authenticated as remote server: This probably should not happen. Remember, the way remote server becomes aware of local posts is by local server pushing those posts to inbox, not by remote server pulling.
        """

        if (request.user.is_authenticated):
            viewingAuthor = Author.objects.get(pk=request.user.author.id)
            postsAuthor = Author.objects.get(pk=author_id)

            if (validateFriends(postsAuthor, viewingAuthor)):
                posts = Post.objects.filter(author=author_id).exclude(
                    visibility=Post.Visibility.UNLISTED).order_by('-published')
                serializer = PostsSerializer(
                    self.paginate_queryset(posts, request), context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

            elif viewingAuthor.id == postsAuthor.id:
                posts = Post.objects.filter(
                    author=author_id).order_by('-published')
                serializer = PostsSerializer(
                    self.paginate_queryset(posts, request), context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

            else:  # not friends and not viewing their own profile
                posts = Post.objects.filter(author=author_id).exclude(visibility=Post.Visibility.FRIENDS).exclude(
                    visibility=Post.Visibility.UNLISTED).order_by('-published')
                serializer = PostsSerializer(
                    self.paginate_queryset(posts, request), context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            posts = Post.objects.filter(author=author_id).exclude(visibility=Post.Visibility.FRIENDS).exclude(
                visibility=Post.Visibility.UNLISTED).order_by('-published')
            serializer = PostsSerializer(
                self.paginate_queryset(posts, request), context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=PostSerializer(),
                         responses={201: PostSerializer},
                         tags=['Posts']
                         )
    def post(self, request, author_id, format=None):
        """Create a new post."""
        try:
            author = Author.objects.get(user=request.user.id)
        except Author.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Author does not exist.'})

        if (not author.approved):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You are not Approved to make a post'})
        # Check that the author_id is the same as the authenticated user
        if (author_id != author.id):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You can only create posts for your own author.'})

        serializer = PostSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save(image=request.data.get('image'))

            follows = Follow.objects.filter(followed=author, pending=False)
            followers = [f.follower for f in follows]

            print("followers: ", followers)

            # Add to follower's inboxes
            if serializer.validated_data['visibility'] == Post.Visibility.FRIENDS:
                # Get all friends of the author (followers that the author is following)
                friends = [f for f in followers if validateFriends(
                    f, author)]

                for friend in friends:
                    print("Sending to friend:" + friend.url + "inbox/")
                    print("Data: ", serializer.data)
                    postToInbox(friend.url + 'inbox/',
                                serializer.data, request)
            elif serializer.validated_data['visibility'] == Post.Visibility.PUBLIC:
                for follower in followers:
                    print("Sending to follower:" + follower.url + "inbox/")
                    print("Data: ", serializer.data)
                    postToInbox(follower.url + 'inbox/',
                                serializer.data, request)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetail(APIView):
    # Allow anyone to read, but must be owner to update Author
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @swagger_auto_schema(responses={200: PostSerializer()}, security=[], tags=['Posts'])
    def get(self, request, author_id, post_id, format=None):
        """Fetch a single post by an author."""

        # TODO: Don't show unlisted or friends-only posts to unauthorized users
        post = get_object_or_404(Post, id=post_id, author=author_id)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=PostSerializer(),
                         responses={200: PostSerializer},
                         tags=['Posts']
                         )
    def put(self, request, author_id, post_id, format=None):
        """Update a single post by an author."""

        post = get_object_or_404(Post, id=post_id, author=author_id)

        self.check_object_permissions(request, post)
        serializer = PostSerializer(
            post, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(responses={204: 'No Content'}, tags=['Posts'])
    def delete(self, request, author_id, post_id, format=None):
        """Delete a single post by an author."""

        post = get_object_or_404(Post, id=post_id, author=author_id)

        self.check_object_permissions(request, post)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT, data={'message': f'Post {post_id} deleted.'})


class PostImage(APIView):
    # Allow anyone to read, but must be owner to update Author
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(responses={200: PostSerializer()}, security=[], tags=['Posts'])
    def get(self, request, author_id, post_id, format=None):
        """Return the image of a post in binary format."""

        # TODO: Don't show unlisted or friends-only posts to unauthorized users
        post = get_object_or_404(Post, id=post_id, author=author_id)

        if post.contentType != 'image/png;base64' and post.contentType != 'image/jpeg;base64':
            return Response(status=status.HTTP_404_BAD_REQUEST, data={'error': 'Image for post not found.'})

        return HttpResponse(post.image, content_type=post.contentType)


class PostLikesList(APIView):

    @swagger_auto_schema(responses={200: LikesSerializer()}, security=[], tags=['Likes', 'Posts'])
    def get(self, request, author_id, post_id, format=None):
        """Fetch a list of likes for a post."""

        likes = Like.objects.filter(post=post_id)
        print(likes)
        serializer = LikesSerializer(
            likes, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentLikesList(APIView):

    @swagger_auto_schema(responses={200: LikeSerializer()}, security=[], tags=['Comments', 'Likes'])
    def get(self, request, author_id, post_id, comment_id, format=None):
        """Fetch a list of likes for a comment."""

        likes = Like.objects.filter(comment=comment_id)
        serializer = LikeSerializer(
            likes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        responses={200: CommentSerializer(many=True)},
        operation_description="Get all comments for a specific post.",
        tags=['Comments'],
        manual_parameters=[PAGE_PARAMETER, SIZE_PARAMETER]
    )
    def get(self, request, author_id, post_id, format=None):
        comments = Comment.objects.filter(post_id=post_id)
        serializer = CommentsSerializer(
            comments,  context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CommentSerializer,
        responses={201: CommentSerializer},
        operation_description="Create a new comment for a specific post.",
        tags=['Comments']
    )
    def post(self, request, author_id, post_id, format=None):

        author = get_object_or_404(Author, pk=author_id)
        if (not author.approved):
            return Response(status=status.HTTP_403_FORBIDDEN, data={'error': 'You are not Approved to make a comment'})

        serializer = CommentSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(post_id=post_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        responses={200: CommentSerializer},
        operation_description="Get a specific comment on a post.",
        tags=['Comments']
    )
    def get(self, request, author_id, post_id, comment_id, format=None):
        comment = get_object_or_404(Comment, post_id=post_id, id=comment_id)
        serializer = CommentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CommentSerializer,
        responses={200: CommentSerializer},
        operation_description="Update a comment for a specific post.",
        tags=['Comments']
    )
    def put(self, request, author_id, post_id, comment_id, format=None):
        comment = get_object_or_404(Comment, post_id=post_id, id=comment_id)

        self.check_object_permissions(request, comment)

        serializer = CommentSerializer(
            comment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={204: 'No Content'},
        operation_description="Delete a specific comment on a post.",
        tags=['Comments']
    )
    def delete(self, request, author_id, post_id, comment_id, format=None):
        comment = get_object_or_404(Comment, post_id=post_id, id=comment_id)

        self.check_object_permissions(request, comment)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def share_post(request, post_id):
    original_post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST' and original_post.visibility == Post.Visibility.PUBLIC:
        # Retrieve the Author instance associated with the current user
        author = get_object_or_404(Author, user=request.user)
        new_post = Post(
            title="Shared: " + original_post.title,
            source=original_post.source,
            origin=original_post.origin,
            description=original_post.description,
            author=author,
            published=timezone.now(),
            visibility=Post.Visibility.PUBLIC,
            contentType=original_post.contentType,
            content=original_post.content
        )
        new_post.save()
        return HttpResponseRedirect(reverse('api:post_list', kwargs={'author_id': str(author.id)}))


class LikeToggle(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Like or unlike a post.",
        responses={200: 'Like added', 204: 'Like removed', 404: 'Not found'}
    )
    def post(self, request, author_id, post_id, **kwargs):
        user = request.user
        post = get_object_or_404(Post, id=post_id)
        author, created = Author.objects.get_or_create(user=user)
        action = request.data.get('action')

        if action == 'like':
            like, created = Like.objects.get_or_create(
                post=post, author=author)
            if created:
                # Serialize the like data for inbox entry
                like_serializer = LikeSerializer(
                    like, context={'request': request})
                self.create_inbox_entry_for_like(
                    post.author, like_serializer.data)
                # Assuming 'post_detail' is the name of your post detail view
                return Response(reverse('client:post_detail', kwargs={'post_id': post_id}))
        elif action == 'unlike':
            like = Like.objects.filter(post=post, author=author)
            if like.exists():
                like.delete()
                return Response(reverse('client:post_detail', kwargs={'post_id': post_id}))
            else:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'error': 'Could not find like object'})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def create_inbox_entry_for_like(self, recipient_author, like_data):
        # Prepare the inbox entry data
        inbox_entry_data = {
            "entry_json": {
                "type": "LIKE",
                "data": like_data
            }
        }
        InboxEntry.objects.create(author=recipient_author, **inbox_entry_data)


class CommentLikeToggle(APIView):
    swagger_auto_schema = None
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        user = request.user
        comment = get_object_or_404(Comment, id=comment_id)
        author, created = Author.objects.get_or_create(user=user)

        like, created = Like.objects.get_or_create(
            comment=comment, author=author)

        if created:
            # If the like was created, the user liked the comment
            return Response({"status": "comment liked"}, status=status.HTTP_201_CREATED)
        else:
            # If the like already existed, remove it (unlike)
            like.delete()
            return Response({"status": "comment unliked"}, status=status.HTTP_204_NO_CONTENT)
