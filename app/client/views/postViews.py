from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.middleware.csrf import get_token
from api.models import Post, Comment, Author, Like
from django.contrib.auth.mixins import LoginRequiredMixin
import requests

from api.utils.postToInbox import postToInbox
from api.serializers.authorSerializer import AuthorSerializer
from api.serializers.postSerializer import CommentSerializer
from api.utils.validation import validateFriends

from ..utils.getAuthorId import getAuthorId

from ..forms.postCreateForm import PostCreateForm
from api.forms import CommentForm


class PostCreateView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        form = PostCreateForm()

        return render(request, 'base.html', {'form': form})

    def post(self, request):
        authorId = getAuthorId(request)
        form = PostCreateForm(request.POST, request.FILES)

        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            visibility = form.cleaned_data['visibility']
            content = form.cleaned_data['content']
            contentType = form.cleaned_data['contentType']

            if 'image' in contentType:
                if not request.FILES.get('image'):
                    form.add_error("image", "Image is required")
                    return render(request, 'posts/post_create.html', {'form': form})

                # Check if image format matches selected image type
                imageFormat = form.cleaned_data['image'].image.format.lower()
                if imageFormat not in contentType:
                    form.add_error(
                        "image", f"Image format must be {contentType}")
                    return render(request, 'posts/post_create.html', {'form': form})
            else:
                if content == "":
                    form.add_error("content", "Content is required")
                    return render(request, 'posts/post_create.html', {'form': form})

            crfsToken = get_token(request)

            # Prepare multipart/form-data payload
            data = {
                'title': title,
                'description': description,
                'visibility': visibility,
                'content': content if content else "image",
                'contentType': contentType,
            }
            files = {'image': request.FILES.get(
                'image')} if request.FILES.get('image') else None

            headers = {'X-CSRFToken': crfsToken,
                       'referer': request.build_absolute_uri('/')}

            response = requests.post(
                request.build_absolute_uri(
                    reverse('api:post_list', kwargs={'author_id': authorId})),
                data=data,
                files=files,
                cookies=request.COOKIES,
                headers=headers
            )

            if response.status_code == 201:
                messages.success(request, "Post created successfully!")
                post = response.json()
                postId = post['id'].split('/')[-1]
                return redirect('client:post_detail', post_id=postId)

            else:
                messages.error(request, f"Error: {response.status_code}")
                return render(request, 'posts/post_create.html', {'form': form})

        return render(request, 'posts/post_create.html', {'form': form})


class PostEditView(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request, post_id):
        postResponse = requests.get(
            request.build_absolute_uri(reverse('api:post_detail', kwargs={
                                       'author_id': getAuthorId(request), 'post_id': post_id})),
            headers={'referer': request.build_absolute_uri('/')}
        )
        post = postResponse.json()
        form = PostCreateForm(initial=post)

        return render(request, 'posts/post_create.html', {'form': form, 'isEdit': True, 'post_id': post_id})

    def post(self, request, post_id):

        authorId = getAuthorId(request)

        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            visibility = form.cleaned_data['visibility']
            content = form.cleaned_data['content']
            contentType = form.cleaned_data['contentType']

            # TODO: Editing of image post is not supported yet

            crfsToken = get_token(request)

            response = requests.put(request.build_absolute_uri(reverse('api:post_detail', kwargs={'author_id': authorId, 'post_id': post_id})),
                                    json={
                "description": description,
                "contentType": contentType,
                "content": content,
                "visibility": visibility,
                "title": title
            }, cookies=request.COOKIES, headers={'X-CSRFToken': crfsToken, 'referer': request.build_absolute_uri('/')})

            if response.status_code == 204:
                return redirect('client:post_detail', post_id=post_id)
            else:
                form.add_error(None, response.status_code)
        else:
            return render(request, 'posts/post_create.html', {'form': form})

        return render(request, 'posts/post_create.html', {'form': form})


class PostDeleteView(LoginRequiredMixin, View):
    login_url = '/login'

    def post(self, request, post_id):
        authorId = getAuthorId(request)
        crfsToken = get_token(request)

        response = requests.delete(request.build_absolute_uri(reverse('api:post_detail', kwargs={'author_id': authorId, 'post_id': post_id})),
                                   cookies=request.COOKIES, headers={'X-CSRFToken': crfsToken, 'referer': request.build_absolute_uri('/')})

        if response.status_code == 204:
            return redirect('client:profile')
        else:
            return HttpResponse(response.status_code)


def post_detail(request, post_id):
    show_comment_form = False  # initially.
    # this is to prevent people from just typing in the link and accesssing the comment form.
    if 'add_comment' in request.GET:
        if not request.user.is_authenticated:
            return redirect('login' + '?next=' + request.path)
        else:
            show_comment_form = True

    post = get_object_or_404(Post, id=post_id)
    author_id = post.author.id
    comments = Comment.objects.filter(post=post)
    likes_count = Like.objects.filter(post=post).count()

    for comment in comments:
        comment.like_count = Like.objects.filter(comment=comment).count()
        comment.user_has_liked = [
            like.author for like in Like.objects.filter(comment=comment)]

    # If post is friends only, check if the current user is friends with the author
    if post.visibility == 'FRIENDS':
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('client:index'))

        if not validateFriends(author1=request.user.author, author2=post.author) and request.user.author != post.author:
            return HttpResponseRedirect(reverse('client:index'))

    # Check if the current user has liked the post
    user_has_liked = False
    if request.user.is_authenticated:
        user_has_liked = Like.objects.filter(
            post=post, author=request.user.author).exists()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'author_id': author_id,
        'comments': comments,
        'show_comment_form': show_comment_form,
        'comment_form': CommentForm(request.POST) if show_comment_form else None,
        'user_has_liked': user_has_liked,
        'likes_count': likes_count,
    })


@login_required
def submit_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    isPostRemote = request.get_host() not in post.origin
    comment_form = CommentForm(request.POST)

    if comment_form.is_valid():
        new_comment = comment_form.save(commit=False)
        new_comment.post = post
        new_comment.author = Author.objects.get(user=request.user)
        new_comment.save()

        commentObj = CommentSerializer(
            new_comment, context={'request': request}).data

        commentObj['id'] = post.origin + '/comments/' + \
            commentObj['id'].split('/')[-1]

        if 'are-you-http' in post.author.url:
            commentObj['author']['url'] = post.author.url[:-1]

        print("CommentObj", commentObj)

        inboxUrl = post.author.url + 'inbox'

        postToInbox(inboxUrl, commentObj, request)

        return HttpResponseRedirect(reverse('client:post_detail', args=[post_id]))

    # handle the case where the form is not valid.
    # this can redirect back to the post detail page or show an error message. Implement it later??
    return HttpResponseRedirect(reverse('client:post_detail', args=[post_id]))


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(
        Comment, id=comment_id, author__user=request.user)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('client:post_detail', post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'posts/edit_comment.html', {'form': form})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(
        Comment, id=comment_id, author__user=request.user)
    post_id = comment.post.id
    comment.delete()
    return HttpResponseRedirect(reverse('client:post_detail', args=[post_id]))


class LikePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        authorURL = post.author.url
        isPostRemote = request.get_host() not in post.origin

        likeObject = {
            "summary": f"{request.user.author.displayName} liked your post",
            "type": "Like",
            "author": AuthorSerializer(request.user.author, context={'request': request}).data,
            "object": post.origin
        }

        # If the post is remote, update remote post copy in our db to reflect the like
        if isPostRemote:
            postToInbox(authorURL + 'inbox', likeObject, request)

            Like.objects.create(
                author=request.user.author, post=post)
        else:
            response = requests.post(
                authorURL + 'inbox',
                json=likeObject,
                cookies=request.COOKIES,
                headers={
                    'X-CSRFToken': get_token(request), 'referer': request.build_absolute_uri('/')}
            )

        return redirect('client:post_detail', post_id=post_id)


class UnlikePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        authorURL = post.author.url

        # If the post is remote, don't allow dislike
        if request.get_host() not in post.origin:
            return redirect('client:post_detail', post_id=post_id)

        like = Like.objects.filter(post=post, author=request.user.author)
        like.delete()

        return redirect('client:post_detail', post_id=post_id)


@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    author = get_object_or_404(Author, user=request.user)
    like = Like.objects.filter(comment=comment, author=author)

    if like.exists():
        like.delete()  # Unlike the comment if like already exists
    else:
        Like.objects.create(comment=comment, author=author)  # Like the comment

    # Redirect back to the post detail page
    return redirect('client:post_detail', post_id=comment.post.id)


def post_likes(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    likes = Like.objects.filter(post=post)
    authors_who_liked = []
    for like in likes:
        authors_who_liked.append(like.author)
    return render(request, 'posts/post_likes.html', {'post': post, 'authors': authors_who_liked})


class SharePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        # Get all followers of the current author
        author_id = getAuthorId(request)
        followerResponse = requests.get(
            request.build_absolute_uri(
                reverse('api:followers_list', kwargs={'author_id': author_id})),
            cookies=request.COOKIES,
            headers={'referer': request.build_absolute_uri('/')}
        )
        followers = followerResponse.json()['items']
        print("Fololower", followers)

        # Get the post
        post = get_object_or_404(Post, id=post_id)
        postAuthorId = post.author.id
        postResponse = requests.get(
            request.build_absolute_uri(reverse('api:post_detail', kwargs={
                                       'author_id': postAuthorId, 'post_id': post_id})),
            headers={'referer': request.build_absolute_uri('/')}
        )

        post = postResponse.json()
        if post['visibility'] != 'PUBLIC':
            return HttpResponseRedirect(reverse('client:post_detail', args=[post_id]))

        print("Attempting to share post object", post)
        # For each follower, post the post to their inbox
        for follower in followers:
            if follower['url'][-1] != '/':
                inboxUrl = follower['url'] + '/inbox'
            else:
                inboxUrl = follower['url'] + 'inbox'

            print('Sharing post to inbox', inboxUrl)
            postToInbox(inboxUrl, post, request)

        messages.success(request, 'Post successfully shared!')

        return HttpResponseRedirect(reverse('client:post_detail', args=[post_id]))
