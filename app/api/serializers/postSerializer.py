
from base64 import b64encode
import uuid
import commonmark
from requests import get
from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method

from ..utils.CustomPagination import CustomPagination

from .authorSerializer import AuthorSerializer

from ..models import Post, Like, Author, Comment


class PostSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="post")
    id = serializers.SerializerMethodField('get_id')
    author = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    commentsSrc = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['type', 'id', 'source', 'origin', 'description', 'contentType',
                  'content', 'author', 'comments', 'commentsSrc', 'published', 'visibility', 'title']

    def get_id(self, obj) -> str:
        return self.context['request'].build_absolute_uri(f"/api/v1/authors/{obj.author.id}/posts/{obj.id}")

    def get_comments(self, obj):
        return self.get_id(obj) + "/comments"

    def get_author(self, obj):
        return AuthorSerializer(obj.author, context=self.context).data

    def get_commentsSrc(self, obj):
        # Get comments for the post
        comments = Comment.objects.filter(post=obj).order_by('-published')
        return CommentsSerializer(comments, context=self.context).data

    def create(self, validated_data):
        author = Author.objects.get(user=self.context['request'].user.id)
        postId = uuid.uuid4()
        source = self.context['request'].build_absolute_uri(
            f"/api/v1/authors/{author.id}/posts/{postId}")
        origin = self.context['request'].build_absolute_uri(
            f"/api/v1/authors/{author.id}/posts/{postId}")

        if validated_data.get('image'):
            image_file = validated_data.pop('image')
            image_binary_data = image_file.read()
            post = Post.objects.create(
                **validated_data, author=author, id=postId, source=source, origin=origin, image=image_binary_data, )
        else:
            post = Post.objects.create(
                **validated_data, author=author, id=postId, source=source, origin=origin)

        return post

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.contentType == Post.ContentType.MARKDOWN:
            parser = commonmark.Parser()
            renderer = commonmark.HtmlRenderer()
            ast = parser.parse(representation['content'])
            representation['content'] = renderer.render(ast)
        return representation


class PostsSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="posts")
    items = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['type', 'items']

    @swagger_serializer_method(serializer_or_field=PostSerializer)
    def get_items(self, obj):
        return PostSerializer(obj, many=True, context=self.context).data


class LikeSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="Like")
    author = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['summary', 'type', 'author', 'object']

    def get_object(self, obj) -> str:
        if obj.post:
            return self.context['request'].build_absolute_uri(f"/api/v1/authors/{obj.author.id}/posts/{obj.post.id}")
        else:
            return self.context['request'].build_absolute_uri(f"/api/v1/authors/{obj.author.id}/posts/{obj.post.id}/comments/{obj.comment.id}")

    def get_summary(self, obj) -> str:
        return f"{obj.author.displayName} liked your post!"

    def get_author(self, obj):
        return AuthorSerializer(obj.author, context=self.context).data


class LikesSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(default="liked")
    items = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = ['type', 'items']

    @swagger_serializer_method(serializer_or_field=LikeSerializer)
    def get_items(self, obj):
        return LikeSerializer(obj, many=True, context=self.context).data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    type = serializers.ReadOnlyField(default="comment")
    id = serializers.SerializerMethodField('get_id')
    contentType = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['type', 'id', 'author',
                  'comment', 'published', 'contentType']
        read_only_fields = ('id', 'published')

    def create(self, data):
        """
        Create and return a new `Comment` instance, given the validated data.
        """
        # Example assumes the existence of a link between the request user and an author
        author = Author.objects.get(user=self.context['request'].user)
        data['author'] = author
        return Comment.objects.create(**data)

    def get_author(self, obj):
        # Adjust according to your Author model's structure
        return AuthorSerializer(obj.author, context=self.context).data

    def get_contentType(self, obj):
        return "text/plain"

    def update(self, instance, data):
        """
        Update and return an existing `Comment` instance, given the validated data.
        """
        instance.comment = data.get('comment', instance.comment)
        # Update other fields if necessary
        instance.save()
        return instance

    def get_id(self, obj) -> str:
        return self.context['request'].build_absolute_uri(f"/api/v1/authors/{obj.author.id}/posts/{obj.post.id}/comments/{obj.id}")


class CommentsSerializer(serializers.ModelSerializer, CustomPagination):
    type = serializers.ReadOnlyField(default="comments")
    page = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['type', 'comments', 'page', 'size']

    @swagger_serializer_method(serializer_or_field=CommentSerializer)
    def get_comments(self, obj):
        return CommentSerializer(self.paginate_queryset(obj, self.context['request']), many=True, context=self.context).data

    def get_page(self, obj):
        page_size = self.get_page_size(self.context['request'])
        paginator = self.django_paginator_class(obj, page_size)
        return self.get_page_number(self.context['request'], paginator)

    def get_size(self, obj):
        return self.get_page_size(self.context['request'])
