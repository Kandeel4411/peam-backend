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


from core.serializers import BaseInvitationSerializer
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


class CourseInvitationSerializer(BaseInvitationSerializer):
    """
    A serializer responsible for handling course invitation instances.

    *Note:* request is expected to be included in the context.
    """

    class Meta(BaseInvitationSerializer.Meta):
        model = CourseInvitation
        fields = BaseInvitationSerializer.Meta.fields + ["email", "course", "type"]
        expandable_fields = dict(
            **BaseInvitationSerializer.Meta.expandable_fields,
            **{
                "course": (
                    "courses.CourseSerializer",
                    {settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ["owner", "title", "code", "description"]},
                ),
            },
        )

    def post_accepted_hook(self, instance: Meta.model, validated_data: dict) -> None:
        user = self.context["request"].user

        # Adding user to either teachers or students if accepted
        if instance.type == CourseInvitationType.TEACHER_INVITE:
            instance.course.teachers.add(user)
        elif instance.type == CourseInvitationType.STUDENT_INVITE:
            instance.course.students.add(user)


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


class TeamInvitationSerializer(BaseInvitationSerializer):
    """
    A serializer responsible for handling team invitation instances.

    *Note:* request is expected to be included in the context.
    """

    class Meta(BaseInvitationSerializer.Meta):
        model = TeamInvitation
        fields = BaseInvitationSerializer.Meta.fields + ["email", "team"]
        expandable_fields = dict(
            **BaseInvitationSerializer.Meta.expandable_fields,
            **{
                "team": (
                    "courses.TeamSerializer",
                    {settings.REST_FLEX_FIELDS["FIELDS_PARAM"]: ["name", "requirement"]},
                ),
            },
        )

    def post_accepted_hook(self, instance: Meta.model, validated_data: dict) -> None:
        user = self.context["request"].user
        instance.team.students.add(user)
