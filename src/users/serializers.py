from allauth.account.models import EmailAddress
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_flex_fields import FlexFieldsModelSerializer


User = get_user_model()


class UserSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling User instances.

    *Note*: request is expected to be passed in the context in case of an update.
    """

    class Meta:
        model = User
        fields = ("uid", "avatar", "username", "email", "first_name", "last_name", "full_name")
        read_only_fields = ("uid", "username")
        extra_kwargs = {"first_name": {"write_only": True}, "last_name": {"write_only": True}}

    def validate(self, data: dict) -> dict:
        if self.instance is not None:  # An instance already exists
            user = self.context["request"].user

            # Only the same user can update the instance
            if self.instance != user:
                raise serializers.ValidationError(
                    detail={"error": _("Only the same user can update his info.")}, code=400
                )

        return super().validate()

    def validate_username(self, username: str) -> str:
        """
        Overriding username validation
        """
        # dj-rest-auth username validation
        return UserDetailsSerializer.validate_username(self, username)

    def update(self, instance: User, validated_data: dict) -> User:
        """
        Custom update method
        """
        avatar = validated_data.get("avatar", None)
        email = validated_data.get("email", None)
        first_name = validated_data.get("first_name", None)
        last_name = validated_data.get("last_name", None)

        updating = {}

        if email is not None:
            # Removing old email address and adding a new one
            EmailAddress._default_manager.get_for_user(instance, instance.email).delete()
            request = self.context["request"]
            EmailAddress._default_manager.add_email(request, instance, email, confirm=True)

            instance.email = email

        # TODO delete old avatar when updating it
        if avatar is not None:
            instance.avatar = avatar
        if first_name is not None:
            instance.first_name = first_name
        if last_name is not None:
            instance.last_name = last_name

        if updating:
            instance.save()

        return instance
