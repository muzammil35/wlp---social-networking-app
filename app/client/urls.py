from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
import requests

from . import views

app_name = 'client'


urlpatterns = [
    # Home is the "Stream" mentioned in spec, shows posts from authors the user follows
    path("", views.home, name="index"),

    # Authors is a page that shows all the authors the server knows about, including authors from registered nodes
    path("authors", views.authors, name="authors"),

    # Inbox is like a notification section, shows relevant shared post, likes, follow request, etc
    path("inbox/", views.InboxView.as_view(), name="inbox"),
    path("inbox/delete", views.InboxDeleteView.as_view(), name="inbox_delete"),
    path("follow/<path:foreign_author_id>/accept",
         views.FollowAcceptView.as_view(), name="follow_accept"),
    path("follow/<path:foreign_author_id>/reject",
         views.FollowDeleteView.as_view(), name="follow_reject"),


    # Profile page shows the user's profile, and the posts they've made. They log out from here.
    path('profile/', views.profile, name='profile'),
    path('profile/<uuid:author_id>/',
         views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<uuid:author_id>/github/',
         views.PollGithubView.as_view(), name='poll_github'),
    path('profile/<uuid:author_id>/edit',
         views.ProfileEditView.as_view(), name='profile_edit'),
    path('profile/<uuid:author_id>/follow',
         views.FollowAuthorView.as_view(), name='follow_profile'),
    path('profile/<uuid:author_id>/unfollow',
         views.UnfollowAuthorView.as_view(), name='unfollow_profile'),

    # Post related routes
    path('posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<uuid:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<uuid:post_id>/share',
         views.SharePostView.as_view(), name='post_share'),
    path('posts/<uuid:post_id>/comment/',
         views.submit_comment, name='submit_comment'),
    path("posts/<uuid:post_id>/likes/", views.post_likes, name="post_likes"),
    path('comments/<uuid:comment_id>/edit/',
         views.edit_comment, name='edit_comment'),
    path('comments/<uuid:comment_id>/delete/',
         views.delete_comment, name='delete_comment'),
    path('comments/<uuid:comment_id>/toggle_like/',
         views.toggle_comment_like, name='toggle_comment_like'),


    path('posts/<uuid:post_id>/edit',
         views.PostEditView.as_view(), name='post_edit'),
    path('posts/<uuid:post_id>/delete',
         views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<uuid:post_id>/like/',
         views.LikePostView.as_view(), name='like_post'),
    path('posts/<uuid:post_id>/unlike/',
         views.UnlikePostView.as_view(), name='unlike_post'),

    # Authentication related routes
    path('register', views.RegisterView.as_view(), name="register"),
    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html', next_page='/profile', redirect_authenticated_user=True), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
