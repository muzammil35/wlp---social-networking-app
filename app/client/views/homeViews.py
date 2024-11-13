from django.shortcuts import render
from django.urls import reverse
import requests
import json
from api.models.node import Node
from ..utils.removeDuplicatePosts import removeDuplicatePosts
from ..utils.sortPosts import sortPosts
from ..utils.getAuthorId import getAuthorId
from django.http import JsonResponse
from datetime import datetime


def home(request):
    posts = []
    authors = []

    # if user is authenticated, show all:
    # local public posts from authors they don't follow
    # post from people they follow (retrieved from inbox)
    print(request.user)

    polling_url = ''

    if request.user.is_authenticated:
        authorId = getAuthorId(request)

        # polling_url = reverse('api:inbox2', kwargs={'author_id': authorId})

        polling_url = request.build_absolute_uri('/')

        print("polling url: ", polling_url)

        response = requests.get(
            request.build_absolute_uri(reverse('api:local_public_post_list')),
            cookies=request.COOKIES,
            headers={'referer': request.build_absolute_uri('/')})

        try:
            posts = response.json().get('items', [])
        except:
            posts = []

        response = requests.get(
            request.build_absolute_uri(
                reverse('api:inbox', kwargs={'author_id': authorId})),
            cookies=request.COOKIES,
            headers={'referer': request.build_absolute_uri('/')})

        try:
            inboxEntries = response.json().get('items', [])
        except:
            inboxEntries = []

        for entry in inboxEntries:
            if entry['type'] == 'post':
                posts.append(entry)

        # There might be duplicate post if the user follows the author of a public post,
        # which is also shared to the user's inbox
        posts = removeDuplicatePosts(posts)
        posts = sortPosts(posts)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            timestamp = request.GET.get('timestamp', None)
            new_posts = []
            if (timestamp and timestamp != '0'):

                timestamp = datetime.fromisoformat(
                    timestamp).replace(tzinfo=None)
                for post in posts:
                    published = datetime.fromisoformat(
                        post['published']).replace(tzinfo=None)
                    # print("timestamp: ", timestamp)
                    # print("published: ", published)
                    if not timestamp or published > timestamp:
                        new_posts.append(post)

            print("new posts before: ", new_posts)
            new_posts = removeDuplicatePosts(new_posts)
            new_posts = sortPosts(new_posts)

            print("new posts: ", new_posts)
            return JsonResponse({'posts': new_posts, 'timestamp': datetime.now().isoformat()})

    # if user is not authenticated, show all authors
    else:
        response = requests.get(
            request.build_absolute_uri(reverse('api:author_list')), headers={'referer': request.build_absolute_uri('/')})
        authors = response.json().get('items', [])

    return render(request, 'home/index.html', {
        'authors': authors,
        'posts': posts,
        'referer_url': request.build_absolute_uri('/'),
        'polling_url': polling_url
    })
