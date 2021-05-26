from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .resources import ResourcesLocator


# ! This is mostly for swagger documentation purposes
class ResourcesLocatorResponseSerializer(serializers.Serializer):
    """
    Custom serializer used to represent response for the resource locator view
    """

    url = serializers.URLField()


class ResourcesLocatorRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent requests for the resource locator view
    """

    resource = serializers.ChoiceField(choices=ResourcesLocator().get_resources())
    uid = serializers.UUIDField()

    def validate(self, data: dict) -> dict:
        locator = ResourcesLocator()
        model = locator.get_model(resource=data["resource"])

        try:
            model._default_manager.get(uid=data["uid"])
        except model.DoesNotExist:
            raise serializers.ValidationError(detail={"uid": "No such object found"}, code=404)
        return data
