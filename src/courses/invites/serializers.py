from allauth.account.adapter import get_adapter
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site


from courses.models import Course, CourseInvitation, TeamStudent, TeamInvitation

User = get_user_model()

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
        read_only_fields = ["token", "sender"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CourseInvitation.objects.all(), fields=["course", "email", "type"]
            )
        ]
        expandable_fields = {
            "sender": "users.UserSerializer",
            "course": (
                "courses.CourseSerializer",
                {settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ["title", "code", "description"]},
            ),
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

            # Can't invite existing teachers and students
            if course.teachers.filter(email=email).exists() or course.students.filter(email=email).exists():
                raise serializers.ValidationError(
                    detail={"email": _("Cant invite someone who already is in the course.")}
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
    """

    status = serializers.ChoiceField(choices=(TeamInvitation.ACCEPTED, TeamInvitation.REJECTED), required=True)

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is None:  # No instance was passed
            raise NotImplementedError("A TeamInvitation instance must be passed to the serializer for validation.")

        instance: TeamInvitation = self.instance

        # Status is already accepted
        if instance.status == TeamInvitation.ACCEPTED:
            raise serializers.ValidationError(detail={"status": _("Invitation is already accepted.")}, code=400)

        # Status is already rejected
        elif instance.status == TeamInvitation.REJECTED:
            raise serializers.ValidationError(detail={"status": _("Invitation is already rejected.")}, code=400)

        # Status is already expired
        elif instance.invitation_expired(save=True):
            raise serializers.ValidationError(detail={"status": _("Invitation is already expired.")}, code=400)

        # Can't join a course where you already exist as a teacher or a student
        if self.instance.course.teachers.filter(email=self.email).exists():
            raise serializers.ValidationError(
                detail={"error": _("Cant join the course where you are already a teacher.")}
            )
        if self.instance.course.students.filter(email=self.email).exists():
            raise serializers.ValidationError(
                detail={"error": _("Cant join the course where you are already a student.")}
            )

        return super().validate(data)


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
        validators = [
            serializers.UniqueTogetherValidator(queryset=TeamInvitation.objects.all(), fields=["team", "email"])
        ]
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
            sender: User = self.context["request"].user
            team = data["team"]
            email: str = data["email"]

            # The sender can't invite himself
            if email == sender.email:
                raise serializers.ValidationError(detail={"email": _("Student can't invite himself to the team")})

            # Only a team student can invite other students
            if not TeamStudent.objects.filter(student=sender, team=team).exists():
                raise serializers.ValidationError(detail={"email": _("Only a team student can invite other students.")})

            # Cant invite someone who belongs to a team in the same requirement
            if TeamStudent.objects.filter(student__email=self.email, team__requirement=self.team.requirement).exists():
                raise serializers.ValidationError(
                    detail={"email": _("Can only invite students that aren't in a team.")}
                )

            # Cant invite a none course student
            if not team.requirement.course.students.filter(email=email).exists():
                raise serializers.ValidationError(
                    detail={"email": _("Can only invite students that are in the course.")}
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
