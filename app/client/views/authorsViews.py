from django.shortcuts import render
from django.urls import reverse
import requests


def authors(request):
    authors = []
    response = requests.get(
        request.build_absolute_uri(reverse('api:author_list')),  headers={'referer': request.build_absolute_uri('/')})
    authors = response.json().get('items', [])

    response = requests.get(
        request.build_absolute_uri(reverse('api:node_author_list')),  headers={'referer': request.build_absolute_uri('/')})
    nodeAuthors = response.json().get('items', [])

    return render(request, 'authors/index.html', {
        'authors': authors + nodeAuthors,
    })
