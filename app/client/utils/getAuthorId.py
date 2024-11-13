from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views import View
from api.models import Post
import requests


def getAuthorId(request):
    """
    Get the authorId of the authenticated user from session if it exists, otherwise 
    fetches the authorId from the API and stores it in the session for future use.
    Also stores the authorId in the session for future use.
    """

    if 'authorId' in request.session:
        return request.session['authorId']

    response = requests.get(
        request.build_absolute_uri(reverse('api:author_list')), headers={'referer': request.build_absolute_uri('/')})
    authors = response.json().get('items', [])
    print(request.user.id)
    print(request.user.author.id)
    authorId = ''

    # Get the authenticated user's author
    for author in authors:
        if author['userId'] == request.user.id:
            authorId = author['id'].split('/')[-1]

            request.session['authorId'] = authorId
            break

    if (authorId == ''):
        return request.user.author.id
    return authorId
