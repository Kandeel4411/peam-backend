import copy

from rest_flex_fields import FlexFieldsModelSerializer
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.models import BaseInvitation
from core.constants import InvitationStatus


class BaseInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling subclassed invitation instances.

    *Note:* request is expected to be included in the context.
    """

    class Meta:
        model = BaseInvitation
        fields = ["token", "sender", "status", "expiry_date", "created_at"]
        read_only_fields = ["token", "sender"]
        expandable_fields = {
            "sender": "users.UserSerializer",
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method. Override this for custom logic for specific invitations
        """
        try:
            if self.instance is not None:  # An instance already exists
                instance: self.Meta.model = copy.deepcopy(self.instance)
                for key, value in data.items():
                    setattr(instance, key, value)
            else:
                sender = self.context["request"].user
                instance = self.Meta.model(**data, sender=sender)
                self.validate_creation_extra(data)
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom updating method
        """
        if "status" not in validated_data:
            raise NotImplementedError("Updating fields other than status isn't currently supported for this serializer")

        # Updating instance status
        instance.status = (invite_status := validated_data["status"])

        # Add to students if accepted
        if invite_status == InvitationStatus.ACCEPTED:
            self.post_accepted_hook(instance, validated_data)

        instance.save()
        return instance

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """
        request = self.context["request"]
        invitation: self.Meta.model = self.Meta.model.send_invitation(
            request=request, sender=request.user, **validated_data
        )
        return invitation

    def post_accepted_hook(self, instance: Meta.model, validated_data: dict) -> None:
        """
        Override this to run a hook method that is going to run once an invitation is accepted.

        Any model instance changes will get saved after this method returns.
        """
        return

    def validate_creation_extra(self, data: dict) -> None:
        """
        Override this to run extra validations than what the base validate provides
        """
        return
