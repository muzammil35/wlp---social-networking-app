from django.contrib import admin
from django.contrib.auth import get_user_model

from .models.follower import Follow

from .models.inboxEntry import InboxEntry
from .models.post import Post, Comment, Like
from .models.node import Node
from .models.author import Author


class PostInstanceInline(admin.TabularInline):
    model = Post
    extra = 0


class CommentInstanceInline(admin.TabularInline):
    model = Comment
    extra = 0


class LikeInstanceInline(admin.TabularInline):
    model = Like
    extra = 0


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('displayName', 'user', 'approved')
    search_fields = ['displayName']

    inlines = [PostInstanceInline, CommentInstanceInline,
               LikeInstanceInline]
    exclude = ["followers"]


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'contentType',
                    'author', 'published', 'visibility')
    list_filter = ['author', 'visibility', 'published']
    search_fields = ['title', 'content']

    fields = ['title', 'source', 'origin', 'description', 'author',
              'visibility', 'contentType', 'content', 'count', 'preview_image', 'published', 'last_modified']
    readonly_fields = ['preview_image', 'published', 'last_modified']


class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'author',
                    'post', 'published')
    list_filter = ['author']
    search_fields = ['comment']


class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'comment', 'author')
    list_filter = ['post', 'comment']


class InboxEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'author')

    ordering = ['-createdAt']


class FollowAdmin(admin.ModelAdmin):
    list_display = ('getFollowed', 'getFollower', 'pending')
    list_filter = ['followed', 'follower', 'pending']
    search_fields = ['followed', 'follower', 'pending']

    @admin.display(description='Followed')
    def getFollowed(self, obj):
        return obj.followed.displayName

    @admin.display(description='Follower')
    def getFollower(self, obj):
        return obj.follower.displayName


admin.site.register(Author, AuthorAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(InboxEntry, InboxEntryAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Node)
