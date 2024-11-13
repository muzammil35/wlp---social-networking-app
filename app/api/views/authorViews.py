import uuid
from django.http import Http404
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
import urllib.parse
from django.contrib.auth.models import User
from rest_framework import permissions

from ..models.node import Node
from ..docs.paginationSchema import PAGE_PARAMETER, SIZE_PARAMETER
from ..utils.CustomPagination import CustomPagination
from ..models.follower import Follow
from ..views.inboxViews import createForeignAuthor
from ..docs.authorSchema import AUTHOR_LIST_REGISTER_REQUEST_BODY
from ..permissions import IsOwnerOrReadOnly
from ..serializers.authorSerializer import AuthorSerializer, AuthorsSerializer
from ..models import Author
from ..serializers.followSerializer import FollowersSerializer, FollowSerializer


class FollowerRequestsListView(APIView):
    swagger_schema = None

    def get(self, request, author_id):
        """
        Get all followers of an author
        """
        # Retrieve the author object based on the provided author_id

        author = get_object_or_404(Author, pk=author_id)
        follows = Follow.objects.filter(followed=author, pending=True)
        followers = [follow.follower for follow in follows]

        # Serialize followers using FollowersSerializer
        serializer = FollowersSerializer(
            followers, context={'request': request})
        # Return serialized data as response
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowersListView(APIView):
    @swagger_auto_schema(security=[], tags=['Follows'], responses={200: FollowersSerializer()})
    def get(self, request, author_id):
        """
        Get all followers of an author
        """
        # Retrieve the author object based on the provided author_id
        author = get_object_or_404(Author, pk=author_id)
        follows = Follow.objects.filter(followed=author, pending=False)
        followers = [follow.follower for follow in follows]

        # Serialize followers using FollowersSerializer
        serializer = FollowersSerializer(
            followers, context={'request': request})
        # Return serialized data as response
        return Response(serializer.data, status=status.HTTP_200_OK)


class FollowerView(APIView):
    def get_follow(self, author_id, foreign_author_id, request):

        foreign_author_id = urllib.parse.unquote(foreign_author_id)
        foreign_author = get_object_or_404(
            Author, url__contains=foreign_author_id)
        author = get_object_or_404(Author, pk=author_id)

        follow = get_object_or_404(
            Follow, follower=foreign_author, followed=author)
        return follow

    @swagger_auto_schema(security=[], tags=['Follows'], responses={200: FollowSerializer(), 404: 'Foreign author does not follow author'})
    def get(self, request, author_id, foreign_author_id):
        '''
        Checks if foreign_author follows author:
        foreign_author follows author -> Follow object in json
        foreign_author does not follo author -> 404
        '''

        follow = self.get_follow(author_id, foreign_author_id, request)

        if follow.pending:
            return Response({'message': 'Follow request pending'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'type': "Follow",
            'actor': AuthorSerializer(follow.follower, context={'request': request}).data,
            'object': AuthorSerializer(follow.followed, context={'request': request}).data,
            'summary': f"{follow.follower.displayName} follows {follow.followed.displayName}"
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(security=[], tags=['Follows'], responses={204: 'Follow request accepted'})
    def put(self, request, author_id, foreign_author_id):
        '''
        Sets the follow relationship from foreign_author_id to author_id as accepted.
        This endpoint is called when user accepts a follow request from foreign_author_id. 
        '''

        follow = self.get_follow(author_id, foreign_author_id, request)
        follow.pending = False
        follow.save()

        foreign_author_id = urllib.parse.unquote(foreign_author_id)
        foreign_author = get_object_or_404(Author, url=foreign_author_id)
        author = get_object_or_404(Author, pk=author_id)

        serializer = FollowSerializer(
            follow, context={'request': request, 'actor': foreign_author, 'object': author})

        return Response(status=status.HTTP_204_NO_CONTENT, data={'message': 'Follow request accepted'})

    @swagger_auto_schema(security=[], tags=['Follows'], responses={204: 'Follow request rejected'})
    def delete(self, request, author_id, foreign_author_id):
        '''
        Deletes the follow relationship from foreign_author_id to author_id.
        This endpoint is called when user rejects a follow request from foreign_author_id
        '''

        follow = self.get_follow(author_id, foreign_author_id, request)
        follow.delete()

        return Response(status=status.HTTP_204_NO_CONTENT, data={'message': 'Follow request rejected'})


class AuthorList(APIView, CustomPagination):
    pagination_class = CustomPagination

    @swagger_auto_schema(responses={200: AuthorsSerializer()}, security=[], tags=['Authors'], manual_parameters=[PAGE_PARAMETER, SIZE_PARAMETER])
    def get(self, request, format=None):
        """List all authors."""

        authors = Author.objects.all().filter(
            url__contains=request.get_host()).order_by('displayName')
        serializer = AuthorsSerializer(
            self.paginate_queryset(authors, request), context={'request': request})

        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(request_body=AUTHOR_LIST_REGISTER_REQUEST_BODY,
                         responses={201: AuthorSerializer,
                                    400: 'Please provide all required fields',
                                    409: 'User already exists'},
                         security=[],
                         tags=['Authors']
                         )
    def post(self, request, format=None):
        """Create a new author."""

        displayName = request.data.get('displayName')
        username = request.data.get('username')
        password = request.data.get('password')
        github = request.data.get('github')
        profile_image = request.data.get('profileImage')

        if not displayName or not username or not password:
            return Response({'error': 'Please provide all required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if (User.objects.filter(username=username).exists()):
            return Response({'error': 'User already exists'}, status=status.HTTP_409_CONFLICT)

        user = User.objects.create_user(username, password=password)
        newAuthorId = uuid.uuid4()
        host = request.build_absolute_uri('/api/v1/')
        url = host + 'authors/' + str(newAuthorId) + '/'
        author = Author.objects.create(
            id=newAuthorId, user=user, displayName=displayName, github=github, profile_image=profile_image, host=host, url=url)

        serializer = AuthorSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuthorDetail(APIView):
    # Allow anyone to read, but must be owner to update Author
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @swagger_auto_schema(responses={200: AuthorSerializer()}, security=[], tags=['Authors'])
    def get(self, request, author_id, format=None):
        """Retrieve the details of a specific author."""

        author = get_object_or_404(Author, pk=author_id)

        serializer = AuthorSerializer(author, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(request_body=AuthorSerializer(),
                         responses={200: AuthorSerializer},
                         tags=['Authors']
                         )
    def put(self, request, author_id, format=None):
        """
        Update the displayName, github or profile_image fields of a specific author.
        Requires the user to be the owner of the author.
        """

        author = get_object_or_404(Author, pk=author_id)
        self.check_object_permissions(request, author)

        author.displayName = request.data.get(
            'displayName', author.displayName)
        author.github = request.data.get('github', author.github)
        author.profile_image = request.data.get(
            'profile_image', author.profile_image)
        author.save()

        print("author", author.profile_image)

        serializer = AuthorSerializer(
            author, context={'request': request})

        return Response(serializer.data)


class NodeAuthorList(APIView):
    swagger_auto_schema = None

    def get(self, request, format=None):
        """List all authors from all nodes, excluding local authors."""
        getNodeAuthors(request)
        authors = Author.objects.all().exclude(
            url__contains=request.get_host()).order_by('displayName')
        serializer = AuthorsSerializer(authors, context={'request': request})
        return Response(serializer.data)


def getNodeAuthors(request):
    """
    Fetches authors from all nodes and creates Author objects for foreign authors if they do not exist.
    """

    nodes = Node.objects.all()

    for node in nodes:
        url = f"{node.url}authors"
        try:
            response = requests.get(url, auth=(node.username, node.password), headers={
                                    'Access-Control-Allow-Origin': '*', 'referer': request.build_absolute_uri('/')}, timeout=5)
            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
            authors_data = response.json()

            for author_json in authors_data.get('items'):
                authorURL = author_json.get('url', '')
                if authorURL[-1] != '/':
                    authorURL += '/'
                authorExists = Author.objects.filter(
                    url=authorURL).exists()
                if not authorExists:
                    foreign_author = createForeignAuthor(author_json)

        except requests.exceptions.RequestException as e:
            # Handle request exceptions, such as connection errors or timeouts
            print(f"Failed to fetch users from node {node.id}: {e}")
