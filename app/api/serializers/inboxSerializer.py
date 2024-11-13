from rest_framework import serializers
from drf_yasg.utils import swagger_serializer_method

from ..models import InboxEntry


class InboxEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = InboxEntry
        fields = '__all__'
