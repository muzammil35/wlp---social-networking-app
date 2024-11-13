from rest_framework import serializers
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_serializer_method

from ..models import Author
from .authorSerializer import AuthorSerializer


class FollowSerializer(serializers.ModelSerializer):

    type = serializers.SerializerMethodField()
    actor = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['type', 'actor', 'object', 'summary']

    def get_type(self, obj):
        return "follow"

    def get_actor(self, obj):
        actor_instance = self.context['actor']
        if actor_instance:
            return AuthorSerializer(actor_instance, context=self.context).data
        return None

    def get_object(self, obj):
        object_instance = self.context['object']
        if object_instance:
            return AuthorSerializer(object_instance, context=self.context).data
        return None

    def get_summary(self, obj):

        # get first part of DisplayName before space
        actor_display_name = self.context['actor'].displayName
        object_display_name = self.context['object'].displayName
        
        return f"{actor_display_name} wants to follow {object_display_name}"
        


class FollowersSerializer(serializers.Serializer):
    items = serializers.SerializerMethodField()
    type = serializers.ReadOnlyField(default="followers")

    class Meta:
        model = Author
        fields = ['type', 'items']

    @swagger_serializer_method(serializer_or_field=FollowSerializer)
    def get_items(self, obj):
        return AuthorSerializer(obj, many=True, context=self.context).data
