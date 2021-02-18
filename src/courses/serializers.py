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
    """

    students = serializers.SlugRelatedField(slug_field="uid", queryset=User.objects.all(), required=True, many=True)

    class Meta:
        model = Team
        fields = ["uid", "name", "requirement", "students"]
        read_only_fields = ["uid"]
        extra_kwargs = {
            "requirement": {"write_only": True},
        }
        validators = [serializers.UniqueTogetherValidator(queryset=Team.objects.all(), fields=["name", "requirement"])]
        expandable_fields = {
            "students": (UserSerializer, {"many": True}),
        }

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """

        if self.instance is not None:  # An instance already exists
            students: list[User] = data.get("students", None)

            if students is not None:
                course = self.instance.requirement.course
                for student in students:
                    # New student must be one of the course students
                    student = course.students.filter(pk=student.pk)
                    if not student.exists():
                        raise serializers.ValidationError(
                            detail={"students": _("All team students must be part of course students.")}
                        )

        else:
            students: list[User] = data["students"]

            course = data["requirement"].course
            for student in students:
                # New student must be one of the course students
                student = course.students.filter(pk=student.pk)
                if not student.exists():
                    raise serializers.ValidationError(
                        detail={"students": _("All team students must be part of course students.")}
                    )
        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom updating method
        """
        students = validated_data.pop("students", None)
        instance: self.Meta.model = super().update(instance, validated_data)

        if students is not None:
            instance.students.set(objs=students)
        return instance

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """

        # Removing "students" to not throw an error and create manually
        students = validated_data.pop("students")

        team: self.Meta.model = super().create(validated_data)

        for student in students:
            TeamStudent.objects.create(team=team, student=student)
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
            serializers.UniqueTogetherValidator(queryset=ProjectRequirement.objects.all(), fields=["title", "course"])
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

    *Note*: request is expected to be passed in the context.
    """

    owner = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=User.objects.all(),
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
        validators = [serializers.UniqueTogetherValidator(queryset=Course.objects.all(), fields=["owner", "code"])]
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
        request_user: User = self.context["request"].user

        if self.instance is not None:  # An instance already exists
            owner: User = data.get("owner", None)

            if owner is not None:
                # Request user must be the same as instance owner if owner is going to be updated
                if request_user.uid != owner.uid:
                    raise serializers.ValidationError(
                        detail={"owner": _("Only the owner can transfer the course to a different user.")}
                    )

                # New owner must be one of the course teachers
                teacher = self.instance.teachers.filter(pk=owner.pk)
                if not teacher.exists():
                    raise serializers.ValidationError(detail={"owner": _("Owner must be one of the course teachers.")})

        else:
            owner: User = data["owner"]

            # owner must be the same as request user
            if request_user != owner:
                raise serializers.ValidationError(detail={"owner": _("Owner must be the same as request user.")})
        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom updating method
        """
        instance.owner = validated_data.get("owner", instance.owner)
        instance.code = validated_data.get("code", instance.code)
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.save()

        return instance

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """

        course: self.Meta.model = super().create(validated_data)

        # Create a course teacher instance for the owner
        CourseTeacher.objects.create(teacher=validated_data["owner"], course=course)

        return course
