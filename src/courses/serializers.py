from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_flex_fields import FlexFieldsModelSerializer

from users.serializers import UserSerializer
from .project_uploading.serializers import ProjectSerializer
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
    """

    students = serializers.SlugRelatedField(slug_field="uid", read_only=True, many=True)
    project = serializers.SlugRelatedField(slug_field="uid", read_only=True)

    class Meta:
        model = Team
        fields = ["uid", "name", "requirement", "students", "project"]
        read_only_fields = ["uid"]
        extra_kwargs = {
            "requirement": {"write_only": True},
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Team._default_manager.all(),
                fields=["name", "requirement"],
                message=_("A team with the same name already exists in the project requirement."),
            )
        ]
        expandable_fields = {"students": (UserSerializer, {"many": True}), "project": ProjectSerializer}

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        try:
            if self.instance is not None:  # An instance already exists
                instance = self.instance

                # Updating requirement is meaningless but is subject to change
                if "requirement" in data:
                    raise serializers.ValidationError(
                        detail={"requirement": _("Can't change a team to a different requirement")}
                    )
            else:
                instance = self.Meta.model(**data)
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


class TeamStudentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling TeamStudent instances
    """

    class Meta:
        model = TeamStudent
        fields = ["student", "team"]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TeamStudent._default_manager.all(),
                fields=["student", "team"],
                message=_("Student already belongs to the team."),
            )
        ]

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


class ProjectRequirementAttachmentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling ProjectRequirementAttachment instances.
    """

    class Meta:
        model = ProjectRequirementAttachment
        fields = ["uid", "title", "requirement", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"requirement": {"write_only": True}}

    def validate(self, data: dict) -> dict:
        """
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


class ProjectRequirementSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling ProjectRequirement instances.
    """

    teams = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)
    attachments = serializers.SlugRelatedField(slug_field="uid", many=True, read_only=True)

    class Meta:
        model = ProjectRequirement
        fields = ["uid", "title", "course", "description", "to_dt", "from_dt", "teams", "attachments", "total_marks"]
        read_only_fields = ["uid", "teams", "attachments"]
        extra_kwargs = {"course": {"write_only": True}}
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ProjectRequirement._default_manager.all(),
                fields=["title", "course"],
                message=_("Can't create multiple project requirements with the same title."),
            )
        ]
        expandable_fields = {
            "teams": (TeamSerializer, {"many": True}),
            "attachments": (ProjectRequirementAttachmentSerializer, {"many": True}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


class CourseAttachmentSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling CourseAttachment instances.
    """

    class Meta:
        model = CourseAttachment
        fields = ["uid", "title", "course", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"course": {"write_only": True}}

    def validate(self, data: dict) -> dict:
        """
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


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
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CourseStudent._default_manager.all(),
                fields=["student", "course"],
                message=_("Student already belongs to the course."),
            )
        ]

    def validate(self, data: dict) -> dict:
        """
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


class CourseTeacherSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling CourseTeacher instances.
    """

    class Meta:
        model = CourseTeacher
        fields = ["teacher", "course"]
        expandable_fields = {
            "teacher": UserSerializer,
        }
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CourseTeacher._default_manager.all(),
                fields=["teacher", "course"],
                message=_("Teacher already belongs to the course."),
            )
        ]

    def validate(self, data: dict) -> dict:
        """
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data


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
            serializers.UniqueTogetherValidator(
                queryset=Course._default_manager.all(),
                fields=["owner", "code"],
                message=_("Owner can't create multiple courses with the same course code"),
            )
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
        Custom validate method
        """
        instance = self.Meta.model(**data) if self.instance is None else self.instance
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data
