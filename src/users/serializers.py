from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling User instances.
    """

    class Meta:
        model = User
        fields = ["uid", "avatar", "username", "email", "first_name", "last_name"]
        read_only_fields = ["uid"]
