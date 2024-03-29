import copy
import zipfile
from typing import List

from rest_framework import serializers
from django.db.models import FileField
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_flex_fields import FlexFieldsModelSerializer

from ..models import Project


# ! This is mostly for swagger documentation purposes
class ProjectFileContentSerializer(serializers.Serializer):
    """
    Custom serializer used to represent responses for project file view.
    """

    content = serializers.CharField(
        help_text="A string representing the file content. Note: will return a "
        "Base64 encoded string if it fails to decode"
    )


class ProjectZipFileFieldSerializer(serializers.Serializer):
    """
    A serializer responsible for displaying project zip file contents.
    """

    files = serializers.ListField(child=serializers.CharField(), read_only=True)

    def validate(self, data: dict) -> dict:
        instance: serializers.FileField = self.instance
        if instance is None:
            raise NotImplementedError("This serializer must have an 'instance' to function")

        assert type(instance) == FileField, "'instance' must be of type FileField"

        try:
            # Checking integrity of zipfile
            with zipfile.ZipFile(instance) as zfile:
                if zfile.testzip() is not None:
                    raise serializers.ValidationError(
                        detail={"project_zip": _("Faulty files were found in the project files.")}, code=500
                    )
        except zipfile.BadZipfile:
            raise serializers.ValidationError(
                detail={
                    "project_zip": _("An unexpected error happened when trying to open the project files."),
                },
                code=500,
            )
        return data

    def to_representation(self, instance: serializers.FileField) -> dict:
        """
        Custom representation method
        """
        with zipfile.ZipFile(instance.file, "r") as zfile:
            return {"files": zfile.namelist()}  # Return list of files & directories in order


class ProjectSerializer(FlexFieldsModelSerializer):
    """
    A serializer responsible for handling project instances.
    """

    class Meta:
        model = Project
        fields = ["uid", "title", "description", "team", "project_zip"]
        read_only_fields = ["uid"]
        expandable_fields = {"team": "courses.TeamSerializer", "project_zip": ProjectZipFileFieldSerializer}

    def validate(self, data: dict) -> dict:
        """
        Custom validation method
        """
        try:
            if self.instance is not None:  # An instance already exists
                instance: self.Meta.model = copy.deepcopy(self.instance)
                for key, value in data.items():
                    setattr(instance, key, value)
            else:
                instance = self.Meta.model(**data)
            instance.full_clean()
        except DjangoValidationError as exc:
            # Converting Django ValidationError to DRF Serializer Validation Error
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))
        return data
