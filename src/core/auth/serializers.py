from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer used in creation of access & refresh tokens.
    """

    @classmethod
    def get_token(cls, user: User) -> dict:
        """
        Overriding get_tokens for adding custom claims.
        """
        token: dict = super().get_token(user)

        token["username"] = user.username
        return token


class CustomRegisterSerializer(RegisterSerializer):
    """
    Custom serializer used in creation / sign up of users.
    """

    # Define transaction.atomic to rollback the save operation in case of error
    @transaction.atomic
    def save(self, request) -> User:
        user: User = super().save(request)
        return user
