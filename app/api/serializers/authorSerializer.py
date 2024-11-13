from rest_framework import serializers
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_serializer_method

from ..models import Author


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class AuthorSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField('get_id')
    userId = serializers.SerializerMethodField()
    type = serializers.ReadOnlyField(default="author")
    profileImage = serializers.CharField(source='profile_image')
    url = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Author
        fields = ['type', 'id', 'userId',
                  'displayName', 'url',
                  'host', 'github', 'profileImage', 'approved']

    def get_id(self, obj) -> str:
        return self.context['request'].build_absolute_uri(f"/api/v1/authors/{obj.id}")

    def get_url(self, obj) -> str:
        if 'are-you-http' in obj.host:
            return obj.url[:-1]

        return obj.url

    def get_type(self, obj) -> str:
        return "author"

    def get_userId(self, obj) -> str:
        if obj.user is None:
            return "0"

        return obj.user.id


class AuthorsSerializer(serializers.ModelSerializer):
    """Serializer for multiple authors and outputting them as JSON that matches project specs."""
    items = serializers.SerializerMethodField()
    type = serializers.ReadOnlyField(default="authors")

    class Meta:
        model = Author
        fields = ['type', 'items']

    @swagger_serializer_method(serializer_or_field=AuthorSerializer)
    def get_items(self, obj):
        return AuthorSerializer(obj, many=True, context=self.context).data
