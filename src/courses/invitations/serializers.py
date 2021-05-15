from allauth.account.adapter import get_adapter
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers, status as status_code
from rest_flex_fields import FlexFieldsModelSerializer
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.validators import UniqueValidator


from core.constants import InvitationStatus
from courses.models import Course, CourseInvitation, TeamStudent, TeamInvitation, CourseStudent, CourseTeacher
from courses.constants import CourseInvitationType

# TODO figure out if status request serializers and response serializer could be generalized instead


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
    type = serializers.ChoiceField(choices=CourseInvitationType.INVITE_CHOICES, required=True)


# ! This is mostly for swagger documentation purposes
class CourseInvitationStatusRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent acceptance/denial status requests for the course invitation view
    """

    status = serializers.ChoiceField(choices=(InvitationStatus.ACCEPTED, InvitationStatus.REJECTED), required=True)


class CourseInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling course invitation instances.

    *Note:* request is expected to be included in the context.
    """

    class Meta:
        model = CourseInvitation
        fields = ["token", "sender", "course", "type", "status", "email", "expiry_date", "created_at"]
        read_only_fields = ["token", "sender"]
        expandable_fields = {
            "sender": "users.UserSerializer",
            "course": (
                "courses.CourseSerializer",
                {settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ["owner", "title", "code", "description"]},
            ),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        try:
            if self.instance is not None:  # An instance already exists
                instance = self.instance
            else:
                sender = self.context["request"].user
                instance = self.Meta.model(**data, sender=sender)

                email: str = data["email"]
                # The sender can't invite himself
                if email == sender.email:
                    raise serializers.ValidationError(detail={"email": _("Sender can't invite himself to the course")})

                course: Course = data["course"]
                invite_type: str = data["type"]
                # If the invite is for a teacher then only the course owner can invite them
                if course.owner != sender and invite_type == CourseInvitationType.TEACHER_INVITE:
                    raise serializers.ValidationError(
                        detail={"type": _("Only the course owner can invite other teachers.")}
                    )
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
        if invite_status == InvitationStatus.ACCEPTED:
            user = self.context["request"].user

            # Adding user to either teachers or students if accepted
            if instance.type == CourseInvitationType.TEACHER_INVITE:
                instance.course.teachers.add(user)
            elif instance.type == CourseInvitationType.STUDENT_INVITE:
                instance.course.students.add(user)

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


class TeamInvitationResponseSerializer(serializers.Serializer):
    """
    Custom serializer used to represent response for team invitation view
    """

    success = serializers.ListField(child=serializers.EmailField(), allow_empty=True, required=True)
    fail = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(), allow_empty=False), allow_empty=True, required=True
    )


# ! This is mostly for swagger documentation purposes and bulk email creation
class TeamInvitationRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent requests for the team invitation view
    """

    emails = serializers.ListField(child=serializers.EmailField(required=True), allow_empty=False, required=True)
    team = serializers.UUIDField(required=True)
    expiry_date = serializers.DateTimeField(label="Expiry Date", required=True)


# ! This is mostly for swagger documentation purposes
class TeamInvitationStatusRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent acceptance/denial status requests for the team invitation view
    """

    status = serializers.ChoiceField(choices=(InvitationStatus.ACCEPTED, InvitationStatus.REJECTED), required=True)


class TeamInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling team invitation instances.

    *Note:* request is expected to be included in the context.
    """

    class Meta:
        model = TeamInvitation
        fields = ["token", "sender", "team", "status", "email", "expiry_date", "created_at"]
        read_only_fields = ["token", "sender"]
        expandable_fields = {
            "sender": "users.UserSerializer",
            "team": ("courses.TeamSerializer", {settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ["name", "requirement"]}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        try:
            if self.instance is not None:  # An instance already exists
                instance = self.instance
            else:
                sender = self.context["request"].user
                instance = self.Meta.model(**data, sender=sender)

                email = data["email"]
                # The sender can't invite himself
                if email == sender.email:
                    raise serializers.ValidationError(detail={"sender": _("Sender can't invite himself to the team")})

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
            user = self.context["request"].user
            instance.team.students.add(user)

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
