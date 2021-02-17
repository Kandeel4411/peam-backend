from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

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


class TeamSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling Team instances.
    """

    members = UserSerializer(source="students", many=True, required=False, read_only=True)
    students = serializers.SlugRelatedField(
        slug_field="uid", queryset=User.objects.all(), required=True, write_only=True, many=True
    )

    class Meta:
        model = Team
        fields = ["uid", "name", "requirement", "students", "members"]
        read_only_fields = ["uid"]
        extra_kwargs = {
            "requirement": {"write_only": True},
        }
        validators = [serializers.UniqueTogetherValidator(queryset=Team.objects.all(), fields=["name", "requirement"])]

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


class ProjectRequirementAttachmentSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling ProjectRequirementAttachment instances.
    """

    class Meta:
        model = ProjectRequirementAttachment
        fields = ["uid", "title", "requirement", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"requirement": {"write_only": True}}


class ProjectRequirementSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling ProjectRequirement instances.
    """

    teams = TeamSerializer(many=True, read_only=True)
    attachments = ProjectRequirementAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectRequirement
        fields = ["uid", "title", "course", "description", "to_dt", "from_dt", "teams", "attachments"]
        read_only_fields = ["uid"]
        extra_kwargs = {"course": {"write_only": True}}
        validators = [
            serializers.UniqueTogetherValidator(queryset=ProjectRequirement.objects.all(), fields=["title", "course"])
        ]


class CourseAttachmentSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling CourseAttachment instances.
    """

    class Meta:
        model = CourseAttachment
        fields = ["uid", "title", "course", "description", "link"]
        read_only_fields = ["uid"]
        extra_kwargs = {"course": {"write_only": True}}


class CourseSerializer(serializers.ModelSerializer):
    """
    A serializer responsible for handling Course instances.

    *Note*: request is expected to be passed in the context.
    """

    owner = UserSerializer(many=False, read_only=True)
    owner_id = serializers.SlugRelatedField(
        slug_field="uid",
        queryset=User.objects.all(),
        help_text=_(
            "`uid` of course owner. Note: request user must be the same as the owner or incase of updating,"
            " the same as the previous owner."
        ),
        required=True,
        write_only=True,
    )
    students = UserSerializer(many=True, read_only=True)
    teachers = UserSerializer(many=True, read_only=True)
    requirements = ProjectRequirementSerializer(many=True, read_only=True)
    attachments = CourseAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "uid",
            "owner",
            "owner_id",
            "title",
            "code",
            "description",
            "students",
            "teachers",
            "requirements",
            "attachments",
        ]
        read_only_fields = ["uid"]
        validators = [serializers.UniqueTogetherValidator(queryset=Course.objects.all(), fields=["owner_id", "code"])]

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        request_user: User = self.context["request"].user

        if self.instance is not None:  # An instance already exists
            owner: User = data.get("owner_id", None)

            if owner is not None:
                # Request user must be the same as instance owner if owner is going to be updated
                if request_user.uid != owner.uid:
                    raise serializers.ValidationError(
                        detail={"owner_id": _("Only the owner can transfer the course to a different user.")}
                    )

                # New owner must be one of the course teachers
                teacher = self.instance.teachers.filter(pk=owner.pk)
                if not teacher.exists():
                    raise serializers.ValidationError(
                        detail={"owner_id": _("Owner must be one of the course teachers.")}
                    )

        else:
            owner: User = data["owner_id"]

            # owner must be the same as request user
            if request_user.uid != owner.uid:
                raise serializers.ValidationError(detail={"owner_id": _("Owner must be the same as request user.")})
        return super().validate(data)

    def update(self, instance: Meta.model, validated_data: dict) -> Meta.model:
        """
        Custom updating method
        """
        instance.owner = (validated_data.get("owner_id", instance.owner),)
        instance.code = (validated_data.get("code", instance.code),)
        instance.title = (validated_data.get("title", instance.title),)
        instance.description = (validated_data.get("description", instance.description),)
        instance.save()

        return instance

    def create(self, validated_data: dict) -> Meta.model:
        """
        Custom creation method
        """

        # Renaming key to "owner" to not throw an error
        validated_data["owner"] = validated_data.pop("owner_id")
        course: self.Meta.model = super().create(validated_data)

        # Create a course teacher instance for the owner
        CourseTeacher.objects.create(teacher=validated_data["owner"], course=course)

        return course
