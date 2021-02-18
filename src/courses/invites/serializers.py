from allauth.account.adapter import get_adapter
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site


from users.serializers import UserSerializer
from courses.models import Course, CourseInvitation

User = get_user_model()


class CourseInvitationResponseSerializer(serializers.Serializer):
    """
    Custom serializer used to represent response for course invitation view
    """

    success = serializers.ListField(child=serializers.EmailField(), allow_empty=True, required=True)
    fail = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(), allow_empty=False), allow_empty=True, required=True
    )


# ! This is mostly for swagger documentation purposes and bulk email creation
class CourseInvitationRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent requests for the course invitation view
    """

    emails = serializers.ListField(child=serializers.EmailField(required=True), allow_empty=False, required=True)
    course = serializers.UUIDField(required=True)
    expiry_date = serializers.DateTimeField(label="Expiry Date", required=True)
    type = serializers.ChoiceField(choices=CourseInvitation.INVITE_CHOICES, required=True)


class CourseInvitationStatusRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent acceptance/denial status requests for the course invitation view
    """

    status = serializers.ChoiceField(choices=(CourseInvitation.ACCEPTED, CourseInvitation.REJECTED), required=True)

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is None:  # No instance was passed
            raise NotImplementedError("A CourseInvitation instance must be passed to the serializer for validation.")

        instance: CourseInvitation = self.instance

        # Status is already accepted
        if instance.status == CourseInvitation.ACCEPTED:
            raise serializers.ValidationError(detail={"status": _("Invitation is already accepted.")}, code=400)

        # Status is already rejected
        elif instance.status == CourseInvitation.REJECTED:
            raise serializers.ValidationError(detail={"status": _("Invitation is already rejected.")}, code=400)

        # Status is already expired
        elif instance.invitation_expired(save=True):
            raise serializers.ValidationError(detail={"expiry_date": _("Invitation is already expired.")}, code=400)

        return super().validate(data)


class CourseInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling course invitation instances.

    *Note:* request is expected to be included in the context.
    """

    sender = serializers.SlugRelatedField(slug_field="uid", many=False, read_only=True)

    class Meta:
        model = CourseInvitation
        fields = ["token", "sender", "course", "type", "status", "email", "expiry_date", "created_at"]
        read_only_fields = ["sender"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CourseInvitation.objects.all(), fields=["course", "email", "type"]
            )
        ]
        expandable_fields = {
            "sender": "users.UserSerializer",
            "course": ("courses.CourseSerializer", {"fields": ["title", "code", "description"]}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is not None:  # An instance already exists
            raise NotImplementedError("Update isn't currently supported for this serializer")

        else:
            sender: User = self.context["request"].user
            invite_type: str = data["type"]
            course: Course = data["course"]
            email: str = data["email"]

            # The owner can't invite himself
            if course.owner.email == email:
                raise serializers.ValidationError(detail={"email": _("Owner can't invite himself to the course")})

            # If the invite is for a teacher then only the course owner can invite them
            if course.owner != sender and invite_type == CourseInvitation.TEACHER_INVITE:
                raise serializers.ValidationError(
                    detail={"type": _("Only the course owner can invite other teachers.")}
                )
            if not course.teachers.filter(pk=sender.pk).exists():
                raise serializers.ValidationError(detail={"sender": _("Only the course teachers can invite.")})

        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom updating method
        """
        raise NotImplementedError("Update isn't currently supported for this serializer")

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """
        request = self.context["request"]
        invitation: self.Meta.model = self.Meta.model.send_invitation(
            request=request, sender=request.user, **validated_data
        )
        return invitation
