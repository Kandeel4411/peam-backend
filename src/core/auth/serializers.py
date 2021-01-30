from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer

from users.models import Student, Teacher

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer used in creation of access & refresh tokens.
    """

    @classmethod
    def get_token(cls, user):
        """
        Overriding get_tokens for adding custom claims.
        """
        token = super().get_token(user)

        token["username"] = user.username

        if hasattr(user, "as_student"):
            token["role"] = "student"
        elif hasattr(user, "as_teacher"):
            token["role"] = "teacher"
        else:
            token["role"] = "anon"

        return token


class CustomRegisterSerializer(RegisterSerializer):
    role = serializers.ChoiceField(required=True, choices=User.USER_ROLE_CHOICES)

    # Define transaction.atomic to rollback the save operation in case of error
    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        role = self.data.get("role")

        if role == User.STUDENT:
            Student.objects.create(user=user)
        elif role == User.TEACHER:
            Teacher.objects.create(user=user)

        return user
