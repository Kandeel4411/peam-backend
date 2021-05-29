import zipfile
import pathlib as pl

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from courses.models import Project
from .sources import SupportedLanguages


class ProjectPlagiarismCompareRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent requests for the project plagiarism compare view.
    """

    first_project = serializers.SlugRelatedField(slug_field="uid", queryset=Project._default_manager.all())
    second_project = serializers.SlugRelatedField(slug_field="uid", queryset=Project._default_manager.all())
    first_file = serializers.CharField(help_text="File path in the first project")
    second_file = serializers.CharField(help_text="File path in the second project")
    match_start_tokens = serializers.CharField(
        required=False,
        default="{",
        help_text="Tokens that will be appended at the start of each marked slice. "
        "If html encoding is enabled then the tokens will be rendered as an unescaped html",
    )
    match_end_tokens = serializers.CharField(
        required=False,
        default="}",
        help_text="Tokens that will be appended at the end of each marked slice. "
        "If html encoding is enabled then the tokens will be rendered as an unescaped html",
    )
    html_encoded = serializers.BooleanField(
        required=False, default=False, help_text="If to return the files contents as html escaped text"
    )

    def validate(self, data: dict) -> dict:

        # Can't check plagiarism for the same project
        if data["first_project"].id == data["second_project"].id:
            raise serializers.ValidationError(
                detail={
                    "first_project": _("Can't compare files in the same project"),
                    "second_project": _("Can't compare files in the same project"),
                }
            )

        first_course = data["first_project"].team.requirement.course_id
        second_course = data["second_project"].team.requirement.course_id

        # Can't check plagiarism for a project in a different course
        if first_course != second_course:
            raise serializers.ValidationError(
                detail={
                    "first_project": _("Project must be in the same course to be able to compare"),
                    "second_project": _("Project must be in the same course to be able to compare"),
                }
            )

        try:
            # Checking integrity of the first project zipfile
            with zipfile.ZipFile(data["first_project"].project_zip.file) as zfile:
                if zfile.testzip() is not None:
                    raise serializers.ValidationError(
                        detail={"first_project": _("Faulty files were found in the project files.")}, code=500
                    )
                fpath = zipfile.Path(zfile, at=data["first_file"])
                # Checking if given file path is an actual file path
                if not fpath.is_file() or not fpath.exists():
                    raise serializers.ValidationError(
                        detail={"first_file": _("Please enter a valid file path in the project")}
                    )
                # Checking if given first file extension is a supported for plagiarism
                elif SupportedLanguages.detect_language(ext=pl.Path(data["first_file"]).suffix) is None:
                    raise serializers.ValidationError(detail={"first_file": _("This file type is not supported")})
        except zipfile.BadZipfile:
            raise serializers.ValidationError(
                detail={
                    "first_project": _("An unexpected error happened when trying to open the project files."),
                },
                code=500,
            )

        try:
            # Checking integrity of the second project zipfile
            with zipfile.ZipFile(data["second_project"].project_zip.file) as zfile:
                if zfile.testzip() is not None:
                    raise serializers.ValidationError(
                        detail={"second_project": _("Faulty files were found in the project files.")}, code=500
                    )
                fpath = zipfile.Path(zfile, at=data["second_file"])
                # Checking if given file path is an actual file path
                if not fpath.is_file() or not fpath.exists():
                    raise serializers.ValidationError(
                        detail={"second_file": _("Please enter a valid file path in the project")}
                    )
                # Checking if given second file extension is a supported for plagiarism
                elif SupportedLanguages.detect_language(ext=pl.Path(data["second_file"]).suffix) is None:
                    raise serializers.ValidationError(detail={"second_file": _("This file type is not supported")})
        except zipfile.BadZipfile:
            raise serializers.ValidationError(
                detail={
                    "second_project": _("An unexpected error happened when trying to open the project files."),
                },
                code=500,
            )
        return data


# ! This is mostly for swagger documentation purposes
class ProjectPlagiarismCompareResponseSerializer(serializers.Serializer):
    """
    Custom serializer used to represent responses for the project plagiarism compare view.
    """

    first_file = serializers.CharField(help_text="Marked plagiarized contents of the first project file")
    second_file = serializers.CharField(help_text="Marked plagiarized contents of the second project file")


# ! This is mostly for swagger documentation purposes
class ProjectPlagiarismRequestSerializer(serializers.Serializer):
    """
    Custom serializer used to represent requests for the project plagiarism view.
    """

    threshold = serializers.DecimalField(
        help_text="Value that is going to be used to filter out ratios that wont meet it. "
        "Can't be greater than 1 or less than 0.3 for accuracy",
        max_digits=3,
        decimal_places=2,
        min_value=0.3,
        max_value=1,
        default=0.3,
        required=False,
        coerce_to_string=False,  # To disable default being a string
    )
    project = serializers.SlugRelatedField(slug_field="uid", queryset=Project._default_manager.all())

    def validate(self, data: dict) -> dict:
        try:
            # Checking integrity of the project zipfile
            with zipfile.ZipFile(data["project"].project_zip.file) as zfile:
                if zfile.testzip() is not None:
                    raise serializers.ValidationError(
                        detail={"project": _("Faulty files were found in the project files.")}, code=500
                    )
        except zipfile.BadZipfile:
            raise serializers.ValidationError(
                detail={
                    "project": _("An unexpected error happened when trying to open the project files."),
                },
                code=500,
            )

        return data


class ProjectPlagiarismMatchSerializer(serializers.Serializer):
    """
    Custom serialized used to represent a match instance for the project plagiarism view.
    """

    file = serializers.CharField(help_text="File path in the project")
    project_title = serializers.CharField(help_text="Project title")
    project = serializers.SlugRelatedField(slug_field="uid", queryset=Project._default_manager.all())
    ratio = serializers.DecimalField(help_text="Plagiarism ratio", max_digits=3, decimal_places=2)


# ! This is mostly for swagger documentation purposes
class ProjectPlagiarismResponseSerializer(serializers.Serializer):
    """
    Custom serializer used to represent responses for the project plagiarism view.
    """

    file = serializers.CharField(help_text="File path in the project")
    matches = serializers.ListField(child=ProjectPlagiarismMatchSerializer(), allow_empty=True)
    failures = serializers.ListField(
        help_text="Project UIDs that plagiarism detection failed to check for some reason",
        child=serializers.SlugRelatedField(slug_field="uid", queryset=Project._default_manager.all()),
        allow_empty=True,
    )
