from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.urls import path
from django.urls import register_converter
from django.urls.converters import StringConverter
from django.core.exceptions import ValidationError
import urllib.parse

from . import views
from .views import LikeToggle, CommentLikeToggle


app_name = 'api'


schema_view = get_schema_view(
    openapi.Info(
        title="We Love Programming! REST API",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    # DRF-Swagger URLs
    path('swagger/', schema_view.with_ui('swagger',
                                         cache_timeout=0), name='schema-swagger-ui'),

    path("authors", views.AuthorList.as_view(), name="author_list"),

    path("authors/", views.AuthorList.as_view(), name="author_list2"),

    path("authors/<uuid:author_id>",
         views.AuthorDetail.as_view(), name="author_detail"),

    path("authors/<uuid:author_id>/posts/",
         views.PostList.as_view(), name="post_list"),

    path("authors/<uuid:author_id>/followers",
         views.FollowersListView.as_view(), name="followers_list"),

    path("authors/<uuid:author_id>/followers/<path:foreign_author_id>/",
         views.FollowerView.as_view(), name="follow"),

    # Used to accomodate grups that don't use trailing slashes
    path("authors/<uuid:author_id>/followers/<path:foreign_author_id>",
         views.FollowerView.as_view(), name="follow2"),

    path("authors/<uuid:author_id>/inbox",
         views.InboxDetail.as_view(), name="inbox"),

    # Used to accomodate grups that don't use trailing slashes
    path("authors/<uuid:author_id>/inbox/",
         views.InboxDetail.as_view(), name="inbox2"),

    path("authors/<uuid:author_id>/posts/<uuid:post_id>/",
         views.PostDetail.as_view(), name="post_detail"),

    path("authors/<uuid:author_id>/posts/<uuid:post_id>/image",
         views.PostImage.as_view(), name="post_image"),

    path('authors/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/like_toggle/',
         CommentLikeToggle.as_view(), name='comment_like_toggle'),

    path("authors/<uuid:author_id>/posts/<uuid:post_id>/likes/",
         views.PostLikesList.as_view(), name="post_like_list"),

    path("authors/<uuid:author_id>/posts/<uuid:post_id>/likes",
         views.PostLikesList.as_view(), name="post_like_list2"),

    # URL for getting all comments for a post or adding a new comment
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/comments/',
         views.CommentListView.as_view(), name='comment-list'),
    # URL for getting, updating, or deleting a specific comment on a post
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/',
         views.CommentDetailView.as_view(), name='comment-detail'),


    # Routes that are used for the frontend. These routes will not show up in the swagger documentation
    path("posts", views.LocalPublicPostList.as_view(),
         name="local_public_post_list"),

    path("authors/<uuid:author_id>/notification/",
         views.NotificationListView.as_view(), name="notifications"),

     path('authors/<uuid:author_id>/check_notifications/',
          views.CheckNewNotifications.as_view(), name='check_new_notifications'),

    path("authors/<uuid:author_id>/follower-requests",
         views.FollowerRequestsListView.as_view(), name="follower_requests"),

    path("node-authors", views.NodeAuthorList.as_view(), name="node_author_list"),
]
