from base64 import b64encode
import datetime
from hmac import new
import re
from django.urls import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
import json
from django.middleware.csrf import get_token
from api.models import Post, Author
from api.serializers.authorSerializer import AuthorSerializer
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
import urllib.parse

from api.models import Node, Follow
from api.utils.postToInbox import postToInbox
from ..forms.registerForm import ProfileEditForm
from ..utils.getAuthorId import getAuthorId


@login_required(login_url='/login')
def profile(request):
    authorId = getAuthorId(request)

    return redirect('client:profile_detail', author_id=authorId)


class ProfileEditView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request, author_id):
        requestAuthorId = getAuthorId(request)

        if str(author_id) != requestAuthorId:
            return redirect('client:profile_detail', author_id=requestAuthorId)

        authorResponse = requests.get(
            request.build_absolute_uri(reverse('api:author_detail', kwargs={'author_id': author_id})),)
        author = authorResponse.json()

        form = ProfileEditForm(initial={
            'displayName': author['displayName'],
            'github': author['github'],
            'profileImage': author['profileImage']
        })

        return render(request, 'profile/edit.html', {
            'author': author,
            'form': form
        })

    def post(self, request, author_id):
        form = ProfileEditForm(request.POST)
        authorResponse = requests.get(
            request.build_absolute_uri(reverse('api:author_detail', kwargs={'author_id': author_id})),)
        author = authorResponse.json()

        if form.is_valid():
            newDisplayName = form.cleaned_data['displayName']
            newGitub = form.cleaned_data['github']
            newProfileImage = form.cleaned_data['profileImage']

            response = requests.put(
                request.build_absolute_uri(
                    reverse('api:author_detail', kwargs={'author_id': author_id})),
                json={
                    "displayName": newDisplayName,
                    "github": newGitub,
                    "profile_image": newProfileImage
                },
                cookies=request.COOKIES,
                headers={'X-CSRFToken': get_token(request),
                         'referer': request.build_absolute_uri('/')}
            )

            if response.status_code == 200:
                return redirect('client:profile_detail', author_id=author_id)
            else:
                form.add_error(
                    None, f"There was an {response.status_code} error with the form")
        else:
            form.add_error(None, "There was an error with the form")

        return render(request, 'profile/edit.html', {
            'author': author,
            'form': form
        })


class ProfileDetailView(View):
    def get(self, request, author_id):
        authorResponse = requests.get(
            request.build_absolute_uri(reverse('api:author_detail', kwargs={'author_id': author_id})), headers={'referer': request.build_absolute_uri('/')})
        author = authorResponse.json()
        authorURL = author.get('url', '')
        isAuthorRemote = request.get_host() not in authorURL

        postsResponse = requests.get(
            request.build_absolute_uri(reverse('api:post_list', kwargs={'author_id': author_id})), headers={'referer': request.build_absolute_uri('/')}, cookies=request.COOKIES)
        posts = postsResponse.json().get('items', [])

        if not request.user.is_authenticated:
            return render(request, 'profile/index.html', {
                'author': author,
                'posts': posts,
                'is_own_profile': False
            })

        # Check if the author is the same as the logged in user
        if author.get('url') == request.user.author.url:
            return render(request, 'profile/index.html', {
                'author': author,
                'posts': posts,
                'is_own_profile': True
            })

        rq_author_path = urllib.parse.quote_plus(request.user.author.url)
        checkAuthorFollowUrl = author.get(
            'url', '')+'followers/'+rq_author_path+"/"
        print("checkAuthorFollowUrl: ", checkAuthorFollowUrl)

        if isAuthorRemote:
            authorHost = authorURL.split('/')[2]
            node = get_object_or_404(Node, url__contains=authorHost)
            print("Node: ", node.url)
            try:
                is_following_author_response = requests.get(
                    checkAuthorFollowUrl, auth=(node.username, node.password), cookies=request.COOKIES, headers={'referer': request.build_absolute_uri('/')}, timeout=5)
            except requests.exceptions.RequestException as e:
                print("Error checking follow response", e)
                is_following_author_response = None
        else:
            is_following_author_response = requests.get(
                checkAuthorFollowUrl, cookies=request.COOKIES, headers={'referer': request.build_absolute_uri('/')}, timeout=3)

        if is_following_author_response.status_code == 200:
            # TODO: Check what other groups are returning as response code
            is_following_author = True
        else:
            is_following_author = False

        is_pending = False
        is_pending = Follow.objects.filter(
            follower=request.user.author, followed=author_id).exists()

        print("Is following author: ", is_following_author)
        print("Is pending: ", is_pending)
        # Unfollowing an remote author would still return the 200 status code
        if is_following_author and not is_pending:
            is_following_author = False

        if not is_following_author:
            posts = [post for post in posts if post.get(
                'visibility', '') == 'PUBLIC']

        return render(request, 'profile/index.html', {
            'author': author,
            'posts': posts,
            'is_own_profile': False,
            'is_following_author': is_following_author,
            'is_pending': is_pending,
        })


class FollowAuthorView(LoginRequiredMixin, View):
    def post(self, request, author_id):
        authorResponse = requests.get(
            request.build_absolute_uri(reverse('api:author_detail', kwargs={'author_id': author_id})), headers={'referer': request.build_absolute_uri('/')})
        author = authorResponse.json()
        authorURL = author.get('url', '')
        isAuthorRemote = request.get_host() not in authorURL

        actor_instance = request.user.author
        object_instance = author

        serialized_follow_data = {
            'type': "Follow",
            'actor': AuthorSerializer(actor_instance, context={'request': request}).data,
            'object': author,
            'summary': f"{actor_instance.displayName} wants to follow {object_instance['displayName']}"
        }

        print("Sending follow request to: ", authorURL+'inbox')
        print("Serialized follow data: ", serialized_follow_data)

        # If author is remote, create a follow object in our own db that assumes the follow is accepted
        # check whether the author is from are-you-http

        if isAuthorRemote:
            if authorURL[-1] != '/':
                postToInbox(authorURL+'/inbox',
                            serialized_follow_data, request)
            else:
                postToInbox(authorURL+'inbox', serialized_follow_data, request)

            followedAuthor = Author.objects.get(id=author_id)
            Follow.objects.create(
                follower=request.user.author, followed=followedAuthor, pending=False)
        else:
            response = requests.post(
                request.build_absolute_uri(
                    reverse('api:inbox', kwargs={'author_id': author_id})),
                json=serialized_follow_data,
                cookies=request.COOKIES,
                headers={'X-CSRFToken': get_token(request),
                         'referer': request.build_absolute_uri('/')}
            )

        return redirect('client:profile_detail', author_id=author_id)


class UnfollowAuthorView(LoginRequiredMixin, View):
    def post(self, request, author_id):
        follow = Follow.objects.filter(
            follower=request.user.author, followed=author_id)
        follow.delete()

        return redirect('client:profile_detail', author_id=author_id)


class PollGithubView(LoginRequiredMixin, View):
    def get(self, request, author_id):
        # Get activity from github from the last 24 hours
        authorResponse = requests.get(
            request.build_absolute_uri(reverse('api:author_detail', kwargs={'author_id': author_id})), headers={'referer': request.build_absolute_uri('/')})
        author = authorResponse.json()

        reqAuthorId = getAuthorId(request)

        if str(author_id) != reqAuthorId:
            return redirect('client:profile_detail', author_id=reqAuthorId)

        github = author.get('github', None)
        if github is None:
            return redirect('client:profile_detail', author_id=author_id)

        githubUsername = github.split('/')[-1]
        githubUrl = f"https://api.github.com/users/{githubUsername}/events"

        response = requests.get(githubUrl)
        newGithubEvents = []
        if response.status_code == 200:
            githubEvents = response.json()

            # Filter events that are from the last 24 hours
            for event in githubEvents:
                yesterday = datetime.datetime.now() - datetime.timedelta(days=30)
                createdAt = datetime.datetime.strptime(
                    event['created_at'], '%Y-%m-%dT%H:%M:%SZ')

                if createdAt > yesterday:
                    newGithubEvents.append(event)

        # Check whther post about github activity is already made
        posts = requests.get(
            request.build_absolute_uri(reverse('api:post_list', kwargs={'author_id': author_id})),  headers={'referer': request.build_absolute_uri('/')})
        posts = posts.json()['items']

        nonDuplicatedEvents = []
        for event in newGithubEvents:
            removeEvent = False
            for post in posts:
                if post['contentType'] == "text/plain" and str(event['id']) in post['content']:
                    removeEvent = True

            if not removeEvent:
                nonDuplicatedEvents.append(event)

        # Create a post for each event
        for event in nonDuplicatedEvents:
            title = f"Github activity: {event['type']}"
            description = f"Event in  {event['repo']['name']}"
            visibility = "PUBLIC"
            content = f"New event: {event['type']} ({event['id']}) in {event['repo']['name']} at {event['created_at']}"
            contentType = "text/plain"

            crfsToken = get_token(request)

            # Prepare multipart/form-data payload
            data = {
                'title': title,
                'description': description,
                'visibility': visibility,
                'content': content,
                'contentType': contentType,
            }
            headers = {'X-CSRFToken': crfsToken,
                       'referer': request.build_absolute_uri('/')}

            response = requests.post(
                request.build_absolute_uri(
                    reverse('api:post_list', kwargs={'author_id': author_id})),
                data=data,
                cookies=request.COOKIES,
                headers=headers
            )

            if response.status_code == 201:
                print("Post created")
            else:
                print("Post not created")

        return redirect('client:profile_detail', author_id=author_id)
