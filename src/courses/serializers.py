from rest_framework import serializers

from projects.serializers import TeamSerializer
from .models import ProjectRequirement, Course, CourseAttachment, ProjectRequirementAttachment


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

    teams = TeamSerializer(required=False, many=True, read_only=True)
    attachments = ProjectRequirementAttachmentSerializer(required=False, many=True, read_only=True)

    class Meta:
        model = ProjectRequirement
        fields = ["uid", "title", "course", "description", "to_dt", "from_dt", "teams", "attachments"]
        read_only_fields = ["uid", "teams", "attachments"]
        extra_kwargs = {"course": {"write_only": True}}


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
    """

    user = serializers.CharField(required=False, read_only=True, source="owner.user.username")
    requirements = ProjectRequirementSerializer(required=False, many=True, read_only=True)
    attachments = CourseAttachmentSerializer(required=False, many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["uid", "owner", "user", "title", "code", "description", "requirements", "attachments"]
        read_only_fields = ["uid", "requirements", "attachments", "user"]
