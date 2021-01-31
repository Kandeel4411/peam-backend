from rest_framework import serializers

from .models import Team


class TeamSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for retrieval and creation of Team instances.
    """

    class Meta:
        model = Team
        fields = ["uid", "name", "requirement"]
        read_only_fields = ["uid"]
        extra_kwargs = {"requirement": {"write_only": True}}
