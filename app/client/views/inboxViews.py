from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token
from django.views import View
import requests

from ..utils.getAuthorId import getAuthorId


class InboxView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        authorId = getAuthorId(request)

        response = requests.get(
            request.build_absolute_uri(
                reverse('api:notifications', kwargs={'author_id': authorId})),
            cookies=request.COOKIES,
            headers={'referer': request.build_absolute_uri('/')})

        followRequests = requests.get(
            request.build_absolute_uri(
                reverse('api:follower_requests',
                        kwargs={'author_id': authorId})
            ),
            cookies=request.COOKIES,
            headers={'referer': request.build_absolute_uri('/')}
        )

        return render(request, 'inbox/index.html', {
            'inboxItems': response.json()['items'],
            'followRequests': followRequests.json()['items']
        })


class InboxDeleteView(LoginRequiredMixin, View):
    login_url = '/login'

    def post(self, request):
        authorId = getAuthorId(request)
        crfsToken = get_token(request)

        response = requests.delete(request.build_absolute_uri(reverse('api:inbox', kwargs={'author_id': authorId})),
                                   cookies=request.COOKIES, headers={'X-CSRFToken': crfsToken, 'referer': request.build_absolute_uri('/')})

        if response.status_code == 204:
            return redirect('client:inbox')
        else:
            return HttpResponse(response.status_code)


class FollowAcceptView(LoginRequiredMixin, View):
    def post(self, request, foreign_author_id):
        authorId = getAuthorId(request)
        crfsToken = get_token(request)

        response = requests.put(request.build_absolute_uri(reverse('api:follow', kwargs={'author_id': authorId, 'foreign_author_id': foreign_author_id})),
                                cookies=request.COOKIES, headers={'X-CSRFToken': crfsToken, 'referer': request.build_absolute_uri('/')})

        if response.status_code == 204:
            return redirect('client:inbox')
        else:
            print("Error: ", response.status_code)
            return redirect('client:inbox')


class FollowDeleteView(LoginRequiredMixin, View):
    def post(self, request, foreign_author_id):
        authorId = getAuthorId(request)
        crfsToken = get_token(request)

        response = requests.delete(request.build_absolute_uri(reverse('api:follow', kwargs={'author_id': authorId, 'foreign_author_id': foreign_author_id})),
                                   cookies=request.COOKIES, headers={'X-CSRFToken': crfsToken, 'referer': request.build_absolute_uri('/')})

        if response.status_code == 204:
            return redirect('client:inbox')
        else:
            return HttpResponse(response.status_code)
