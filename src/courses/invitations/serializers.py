from allauth.account.adapter import get_adapter
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers, status as status_code
from rest_flex_fields import FlexFieldsModelSerializer
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
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


class CourseInvitationStatusRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent acceptance/denial status requests for the course invitation view

    *Note:* request is expected to be in included in the context.
    """

    status = serializers.ChoiceField(choices=(InvitationStatus.ACCEPTED, InvitationStatus.REJECTED), required=True)

    class Meta:
        model = CourseInvitation

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is None:  # No instance was passed
            raise NotImplementedError("A CourseInvitation instance must be passed to the serializer for validation.")

        instance: self.Meta.model = self.instance

        # Status is already accepted
        if instance.status == InvitationStatus.ACCEPTED:
            raise serializers.ValidationError(
                detail={"status": _("Invitation is already accepted.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        # Status is already rejected
        elif instance.status == InvitationStatus.REJECTED:
            raise serializers.ValidationError(
                detail={"status": _("Invitation is already rejected.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        # Status is already expired
        elif instance.invitation_expired(save=True):
            raise serializers.ValidationError(
                detail={"expiry_date": _("Invitation is already expired.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom update method
        """
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


class CourseInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling course invitation instances.

    *Note:* request is expected to be included in the context.
    """

    sender = serializers.SlugRelatedField(slug_field="uid", many=False, read_only=True)

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
        if self.instance is not None:  # An instance already exists
            raise NotImplementedError("Update isn't currently supported for this serializer")
        else:
            email: str = data["email"]
            course: Course = data["course"]
            sender = self.context["request"].user
            invite_type: str = data["type"]

            # Expiry date can't be less than the creation date
            if data["expiry_date"] <= timezone.localtime():
                raise serializers.ValidationError(
                    detail={"expiry_date": _("Expiry date can't be less than the creation date.")}
                )

            # The sender can't invite himself
            if email == sender.email:
                raise serializers.ValidationError(detail={"email": _("Sender can't invite himself to the course")})

            # If the invite is for a teacher then only the course owner can invite them
            if course.owner != sender and invite_type == CourseInvitationType.TEACHER_INVITE:
                raise serializers.ValidationError(
                    detail={"type": _("Only the course owner can invite other teachers.")}
                )

            # Enforcing that if already in the course as either a student or a teacher then return an error
            if CourseStudent._default_manager.filter(student__email=email, course_id=course.uid).exists():
                raise serializers.ValidationError(
                    detail={"email": _("A course student with this email already exists.")},
                )
            elif CourseTeacher._default_manager.filter(teacher__email=email, course_id=course.uid).exists():
                raise serializers.ValidationError(
                    detail={"email": _("A course teacher with this email already exists.")},
                )

            # Enforcing the uniqueness of email to course if an existing invite didn't expire or was rejected
            # and accepted Note: The reason why we aren't checking on accepted is because of this scenario:
            # a user changed his email and created another account with the old email which would render
            # the previously accepted invitation invalid for the old email.
            if self.Meta.model._default_manager.filter(
                email=email, course_id=course.uid, status=InvitationStatus.PENDING
            ).exists():
                raise serializers.ValidationError(
                    detail={"email": _("A course invitation with this email already exists that is pending.")}
                )

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


class TeamInvitationStatusRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent acceptance/denial status requests for the team invitation view

    *Note:* request is expected to be in included in the context.
    """

    status = serializers.ChoiceField(choices=(InvitationStatus.ACCEPTED, InvitationStatus.REJECTED), required=True)

    class Meta:
        model = TeamInvitation

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is None:  # No instance was passed
            raise NotImplementedError("A TeamInvitation instance must be passed to the serializer for validation.")

        instance: self.Meta.model = self.instance
        user = self.context["request"].user

        # Status is already accepted
        if instance.status == InvitationStatus.ACCEPTED:
            raise serializers.ValidationError(
                detail={"status": _("Invitation is already accepted.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        # Status is already rejected
        elif instance.status == InvitationStatus.REJECTED:
            raise serializers.ValidationError(
                detail={"status": _("Invitation is already rejected.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        # Status is already expired
        elif instance.invitation_expired(save=True):
            raise serializers.ValidationError(
                detail={"status": _("Invitation is already expired.")}, code=status_code.HTTP_400_BAD_REQUEST
            )

        # Can't join a course where you already exist as a teacher or a student
        if CourseTeacher._default_manager.filter(teacher_id=user.uid, course_id=instance.course_id).exists():
            raise serializers.ValidationError(
                detail={"error": _("Cant join the course where you are already a teacher.")}
            )
        if CourseStudent._default_manager.filter(student_id=user.uid, course_id=instance.course_id).exists():
            raise serializers.ValidationError(
                detail={"error": _("Cant join the course where you are already a student.")}
            )

        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom update method
        """
        # Updating instance status
        instance.status = (invite_status := validated_data["status"])

        # Add to students if accepted
        if invite_status == InvitationStatus.ACCEPTED:
            user = self.context["request"].user
            instance.team.students.add(user)

        instance.save()


class TeamInvitationSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling team invitation instances.

    *Note:* request is expected to be included in the context.
    """

    sender = serializers.SlugRelatedField(slug_field="uid", many=False, read_only=True)

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
        if self.instance is not None:  # An instance already exists
            raise NotImplementedError("Update isn't currently supported for this serializer")
        else:
            sender = self.context["request"].user
            team = data["team"]
            email = data["email"]

            # The sender can't invite himself
            if email == sender.email:
                raise serializers.ValidationError(detail={"sender": _("Sender can't invite himself to the team")})

            # Enforcing that a student can only belong to one team in each project requirement
            if TeamStudent._default_manager.filter(
                student__email=email, team__requirement_id=team.requirement_id
            ).exists():
                raise serializers.ValidationError(
                    detail={"email": _("A team student with this email already exists.")},
                )

            # Cant invite a none course student
            if not CourseStudent._default_manager.filter(student__email=email, course_id=team.course_id).exists():
                raise serializers.ValidationError(
                    detail={"email": _("Can only invite students that are in the course.")}
                )

            # Enforcing the uniqueness of email to team if an existing invite didn't expire or was rejected
            # and accepted Note: The reason why we aren't checking on accepted is because of this scenario:
            # a user changed his email and created another account with the old email which would render
            # the previously accepted invitation invalid for the old email.
            if self.Meta.model._default_manager.filter(
                email=email, team_id=team.uid, status=InvitationStatus.PENDING
            ).exists():
                raise serializers.ValidationError(
                    detail={"email": _("A team invitation with this email already exists that is pending.")}
                )

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
