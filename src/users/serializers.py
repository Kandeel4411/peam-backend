from typing import Optional

from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from dj_rest_auth.serializers import UserDetailsSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling User instances.
    """

    full_name = serializers.SerializerMethodField("get_full_name", read_only=True, required=False)

    class Meta:
        model = User
        fields = ("uid", "avatar", "username", "email", "first_name", "last_name", "full_name")
        read_only_fields = ("uid", "email")
        extra_kwargs = {"first_name": {"write_only": True}, "last_name": {"write_only": True}}

    def get_full_name(self, obj: Meta.model) -> Optional[str]:
        """
        Method that returns the full name of the user
        """
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return None

    def validate_username(self, username: str) -> str:
        """
        Overriding username validation
        """
        # dj-rest-auth username validation
        return UserDetailsSerializer.validate_username(self, username)
