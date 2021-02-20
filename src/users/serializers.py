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
        fields = ("uid", "avatar", "username", "email", "name")
        read_only_fields = ("uid", "username")

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
        name = validated_data.get("name", None)

        updating = {}

        if email is not None and email != instance.email:
            # Removing old email address and adding a new one
            EmailAddress._default_manager.get_for_user(instance, instance.email).delete()
            request = self.context["request"]
            EmailAddress._default_manager.add_email(request, instance, email, confirm=True)

            updating["email"] = email

        # TODO delete old avatar when updating it
        if avatar is not None and avatar != instance.avatar:
            updating["avatar"] = avatar
        if name is not None and instance.name != name:
            updating["name"] = name

        if updating:
            for key, value in updating.items():
                setattr(instance, key, value)
            instance.save()

        return instance
