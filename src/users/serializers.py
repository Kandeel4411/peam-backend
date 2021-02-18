from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_flex_fields import FlexFieldsModelSerializer


User = get_user_model()


class UserSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling User instances.
    """

    class Meta:
        model = User
        fields = ("uid", "avatar", "username", "email", "first_name", "last_name", "full_name")
        read_only_fields = ("uid", "email")
        extra_kwargs = {"first_name": {"write_only": True}, "last_name": {"write_only": True}}

    def validate_username(self, username: str) -> str:
        """
        Overriding username validation
        """
        # dj-rest-auth username validation
        return UserDetailsSerializer.validate_username(self, username)
