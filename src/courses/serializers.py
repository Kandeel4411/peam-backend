from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_flex_fields import FlexFieldsModelSerializer

from users.serializers import UserSerializer
from .models import (
    ProjectRequirement,
    Course,
    CourseAttachment,
    ProjectRequirementAttachment,
    CourseStudent,
    CourseTeacher,
    Team,
    TeamStudent,
)


User = get_user_model()


class TeamSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling Team instances.

    *Note*: request is expected to be passed in the context.
    """

    students = serializers.SlugRelatedField(
        slug_field="uid", queryset=User._default_manager.all(), required=True, many=True
    )

    class Meta:
        model = Team
        fields = ["uid", "name", "requirement", "students"]
        read_only_fields = ["uid", "students"]
        extra_kwargs = {
            "requirement": {"write_only": True},
        }
        validators = [
            serializers.UniqueTogetherValidator(queryset=Team._default_manager.all(), fields=["name", "requirement"])
        ]
        expandable_fields = {
            "students": (UserSerializer, {"many": True}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        request_user: User = self.context["request"].user

        if self.instance is not None:  # An instance already exists
            pass
        else:
            student = request_user
            requirement = data["requirement"]

            # Enforcing that student can only belong to one team in each project requirement
            if TeamStudent._default_manager.filter(
                student_id=student.uid, team__requirement_id=requirement.uid
            ).exists():
                raise serializers.ValidationError(
                    detail={"error": _("User already belongs to another team.")},
                )

        return super().validate(data)

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """

        team: self.Meta.model = super().create(validated_data)

        # Adding request user as a student to the
        request = self.contest["request"]
        TeamStudent._default_manager.create(team_id=team.uid, student_id=request.user.uid)

        return team


class ProjectRequirementAttachmentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling ProjectRequirementAttachment instances.
    """

    class Meta:
        model = ProjectRequirementAttachment
        fields = ["uid", "title", "requirement", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"requirement": {"write_only": True}}


class ProjectRequirementSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling ProjectRequirement instances.
    """

    teams = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)
    attachments = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)

    class Meta:
        model = ProjectRequirement
        fields = ["uid", "title", "course", "description", "to_dt", "from_dt", "teams", "attachments"]
        read_only_fields = ["uid", "teams", "attachments"]
        extra_kwargs = {"course": {"write_only": True}}
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ProjectRequirement._default_manager.all(), fields=["title", "course"]
            )
        ]
        expandable_fields = {
            "teams": (TeamSerializer, {"many": True}),
            "attachments": (ProjectRequirementAttachmentSerializer, {"many": True}),
        }


class CourseAttachmentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling CourseAttachment instances.
    """

    class Meta:
        model = CourseAttachment
        fields = ["uid", "title", "course", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"course": {"write_only": True}}


class CourseStudentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling CourseStudent instances.
    """

    class Meta:
        model = CourseStudent
        fields = ["student", "course"]
        read_only_fields = ["course", "student"]
        expandable_fields = {
            "student": UserSerializer,
        }


class CourseTeacherSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling CourseTeacher instances.
    """

    class Meta:
        model = CourseTeacher
        fields = ["teacher", "course"]
        read_only_fields = ["course", "teacher"]
        expandable_fields = {
            "teacher": UserSerializer,
        }


class CourseSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling Course instances.
    """

    owner = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=User._default_manager.all(),
        help_text=_(
            "`uid` of course owner. Note: request user must be the same as the owner or incase of updating,"
            " the same as the previous owner."
        ),
        required=True,
    )
    students = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)
    teachers = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)
    requirements = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)
    attachments = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "uid",
            "owner",
            "title",
            "code",
            "description",
            "students",
            "teachers",
            "requirements",
            "attachments",
        ]
        read_only_fields = ["uid", "teachers", "students", "requirements", "attachments"]
        validators = [
            serializers.UniqueTogetherValidator(queryset=Course._default_manager.all(), fields=["owner", "code"])
        ]
        expandable_fields = {
            "owner": UserSerializer,
            "students": (UserSerializer, {"many": True}),
            "teachers": (UserSerializer, {"many": True}),
            "requirements": (ProjectRequirementSerializer, {"many": True}),
            "attachments": (CourseAttachmentSerializer, {"many": True}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        if self.instance is not None:  # An instance already exists
            pass
        else:
            pass
        return super().validate(data)

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """

        course: self.Meta.model = super().create(validated_data)

        # Create a course teacher instance for the owner
        CourseTeacher._default_manager.create(teacher_id=course.owner_id, course_id=course.uid)

        return course
