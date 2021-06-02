import zipfile
import pathlib as pl

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from tree_sitter import TreeCursor

from core.utils.openapi import openapi_error_response
from courses.models import Project
from courses.utils import is_course_teacher
from .serializers import (
    ProjectPlagiarismRequestSerializer,
    ProjectPlagiarismResponseSerializer,
    ProjectPlagiarismMatchSerializer,
    ProjectPlagiarismCompareRequestSerializer,
    ProjectPlagiarismCompareResponseSerializer,
)
from .tokens import Token, parse_tree
from .sources import parse_source, match_sequences, tokenize_source, SupportedLanguages, detect_plagiarism_ratio


class ProjectPlagiarismView(APIView):
    """
    Base view for project plagiarism.
    """

    @swagger_auto_schema(
        request_body=ProjectPlagiarismRequestSerializer(),
        responses={
            status.HTTP_200_OK: ProjectPlagiarismResponseSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi_error_response(
                description="Internal server errors",
                examples={"property": "Faulty files were found in the project files."},
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Detects plagiarism for all the supported files in a specific project.

        .
        """

        request_serializer = ProjectPlagiarismRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        data = request_serializer.data
        project_id = data["project"]
        threshold = data["threshold"]

        project = Project._default_manager.get(uid=project_id)

        # Only course teachers can view plagiarism
        authorized = is_course_teacher(user=request.user, course_id=project.team.requirement.course_id)
        if not authorized:
            message = _("Only course teachers can view plagiarism")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        # Only look through the other projects in the same requirement
        other_projects = (
            Project._default_manager.exclude(uid=project_id)
            .filter(team__requirement_id=project.team.requirement_id)
            .all()
        )

        data = {"files": []}

        # For calculating avg ratio for files
        total_ratio = 0
        total_files = 0

        with zipfile.ZipFile(project.project_zip.file, "r") as zfile:
            files = zfile.namelist()
            for _file in files:  # Looping over all possible project files
                fpath = zipfile.Path(zfile, at=_file)
                fext = pl.Path(_file).suffix

                # Checking if current object is a file and is a supported type
                if not fpath.is_file():
                    continue
                elif not SupportedLanguages.detect_language(ext=fext):
                    continue

                with fpath.open("rb") as f:
                    source = f.read().decode("utf-8")
                    if not len(source):
                        continue  # Ignore empty file

                total_files += 1

                _data = {"file": _file, "failures": [], "matches": []}

                # For calculating avg ratio for file matches
                _total_ratio = 0
                _total_files = 0

                # Looping over all the other possible projects
                for other_project in other_projects:
                    try:
                        with zipfile.ZipFile(other_project.project_zip.file, "r") as other_zfile:
                            other_files = other_zfile.namelist()
                            for other_file in other_files:
                                other_fpath = zipfile.Path(other_zfile, at=other_file)
                                if not other_fpath.is_file():
                                    continue
                                elif fext != pl.Path(other_file).suffix:
                                    continue

                                with other_fpath.open("rb") as other_f:
                                    other_source = other_f.read().decode("utf-8")
                                    if not len(other_source):
                                        continue  # Ignore empty file

                                plag_ratio = detect_plagiarism_ratio(source1=source, source2=other_source, ext=fext)

                                if plag_ratio < threshold:
                                    continue

                                _total_ratio += plag_ratio
                                _total_files += 1

                                _data["matches"].append(
                                    {
                                        "project": other_project,
                                        "file": other_file,
                                        "ratio": plag_ratio,
                                        "project_title": other_project.title,
                                    }
                                )

                    except zipfile.BadZipfile:
                        _data["failures"].append(other_project.uid)

                if _total_files:
                    _data["ratio"] = _total_ratio / _total_files
                    total_ratio += _data["ratio"]
                    data["files"].append(_data)

        if total_files:
            data["ratio"] = total_ratio / total_files
        serializer = ProjectPlagiarismResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectPlagiarismCompareView(APIView):
    """
    Base view for project plagiarism file comparison
    """

    @swagger_auto_schema(
        request_body=ProjectPlagiarismCompareRequestSerializer(),
        responses={
            status.HTTP_200_OK: ProjectPlagiarismCompareResponseSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi_error_response(
                description="Internal server errors",
                examples={"property": "Faulty files were found in the project files."},
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Detects plagiarism for two specific project files and returns plagiarized marked content.

        .
        """

        request_serializer = ProjectPlagiarismCompareRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        data: dict = request_serializer.data

        first_project = Project._default_manager.get(uid=data["first_project"])
        second_project = Project._default_manager.get(uid=data["second_project"])
        first_file: str = data["first_file"]
        second_file: str = data["second_file"]

        # Only course teachers can view plagiarism
        authorized = is_course_teacher(user=request.user, course_id=first_project.team.requirement.course_id)
        if not authorized:
            message = _("Only course teachers can view plagiarism")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        with zipfile.ZipFile(first_project.project_zip.file, "r") as zfile:
            with zfile.open(first_file, "r") as f:
                first_source = f.read().decode("utf-8")

        with zipfile.ZipFile(second_project.project_zip.file, "r") as zfile:
            with zfile.open(second_file, "r") as f:
                second_source = f.read().decode("utf-8")

        fext = pl.Path(first_file).suffix
        first_tree: TreeCursor = parse_source(source=first_source, ext=fext)
        second_tree: TreeCursor = parse_source(source=second_source, ext=fext)

        first_parse: list[Token] = parse_tree(first_tree.walk(), child_only=False)
        second_parse: list[Token] = parse_tree(second_tree.walk(), child_only=False)
        marked_first_source, marked_second_source, ratio = match_sequences(
            tokens1=first_parse,
            tokens2=second_parse,
            source1=first_source,
            source2=second_source,
        )

        response = {}
        response["first_file"] = tokenize_source(
            source=first_source,
            marked_source=marked_first_source,
            start_tokens=data["match_start_tokens"],
            end_tokens=data["match_end_tokens"],
            html_encoded=data["html_encoded"],
        )
        response["second_file"] = tokenize_source(
            source=second_source,
            marked_source=marked_second_source,
            start_tokens=data["match_start_tokens"],
            end_tokens=data["match_end_tokens"],
            html_encoded=data["html_encoded"],
        )
        serializer = ProjectPlagiarismCompareResponseSerializer(response)
        return Response(serializer.data, status=status.HTTP_200_OK)
