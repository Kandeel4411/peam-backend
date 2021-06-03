import zipfile
import base64

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import status
from rest_flex_fields import is_expanded
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from core.utils.openapi import openapi_error_response
from ..models import Project
from ..utils import is_team_student, is_course_teacher, is_course_student
from .serializers import ProjectSerializer, ProjectFileContentSerializer, ProjectZipFileFieldSerializer


class ProjectFileView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for project files.
    """

    queryset = Project._default_manager.all()
    serializer_class = ProjectSerializer
    lookup_fields = {
        "course_owner": "team__requirement__course__owner__username",
        "course_code": "team__requirement__course__code",
        "requirement_title": "team__requirement__title",
        "team_name": "team__name",
        "project_title": {"filter_kwarg": "title", "pk": True},
    }

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: ProjectZipFileFieldSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Request specific errors",
                examples={"error": "Path must be valid file path in the project."},
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Displays a list of the project files.

        .
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        instance: Project = self.get_object()

        # Only those who belong to the course can retrieve
        authorized: bool = is_course_teacher(
            user=request.user, owner_username=username, code=code
        ) or is_course_student(user=request.user, owner_username=username, code=code)
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectZipFileFieldSerializer(instance=instance.project_zip)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectFileDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project file.
    """

    queryset = Project._default_manager.all()
    serializer_class = ProjectSerializer
    lookup_fields = {
        "course_owner": "team__requirement__course__owner__username",
        "course_code": "team__requirement__course__code",
        "requirement_title": "team__requirement__title",
        "team_name": "team__name",
        "project_title": {"filter_kwarg": "title", "pk": True},
    }

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: ProjectFileContentSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Request specific errors",
                examples={"error": "Path must be valid file path in the project."},
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Displays project file contents.

        .
        """
        path: str = kwargs["path"]
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        instance: Project = self.get_object()

        # Only those who belong to the course can retrieve
        authorized: bool = is_course_teacher(
            user=request.user, owner_username=username, code=code
        ) or is_course_student(user=request.user, owner_username=username, code=code)
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        data = {}
        try:
            with zipfile.ZipFile(instance.project_zip.file) as zfile:
                zpath = zipfile.Path(zfile, at=path)
                if not zpath.is_file():
                    return Response({"error": "Path must be valid file path in the project."})

                try:
                    with zpath.open("r") as f:
                        try:
                            content = f.read()
                            data["content"] = content.decode("utf-8")
                        except UnicodeDecodeError:
                            data["content"] = str(base64.b64encode(content))[2:-1]

                except KeyError:
                    return Response({"error": "Path must be a valid file path in the project."})
        except zipfile.BadZipFile:
            return Response({"error": "Unexpected error happened while trying to read project files."})

        serializer = ProjectFileContentSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for projects.
    """

    queryset = Project._default_manager.all()
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = ProjectSerializer
    lookup_fields = {
        "course_owner": "team__requirement__course__owner__username",
        "course_code": "team__requirement__course__code",
        "requirement_title": "team__requirement__title",
        "team_name": "team__name",
    }

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectSerializer(),
        responses={
            status.HTTP_201_CREATED: ProjectSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]
        title: str = kwargs["requirement_title"]

        # Only team members can create a project
        authorized = is_team_student(user=request.user, owner_username=username, code=code, requirement_title=title)
        if not authorized:
            message = _("Only team members can create a project")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project.
    """

    queryset = Project._default_manager.all()
    serializer_class = ProjectSerializer
    lookup_fields = {
        "course_owner": "team__requirement__course__owner__username",
        "course_code": "team__requirement__course__code",
        "requirement_title": "team__requirement__title",
        "team_name": "team__name",
        "project_title": {"filter_kwarg": "title", "pk": True},
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "team"):
            queryset = queryset.prefetch_related("team")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: ProjectSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, owner_username=username, code=code) or is_course_student(
            user=request.user, owner_username=username, code=code
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectSerializer(),
        responses={
            status.HTTP_200_OK: ProjectSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a project.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        instance = self.get_object()

        # Only course teachers and team members can update or delete a project
        authorized = is_course_teacher(user=request.user, owner_username=username, code=code) or is_team_student(
            user=request.user, team_id=instance.team_id
        )
        if not authorized:
            message = _("Only course teachers and team members can update or delete a team.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_204_NO_CONTENT: "",
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        }
    )
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project.

        Removes related objects
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        instance = self.get_object()

        # Only course teachers and team members can update or delete a project
        authorized = is_course_teacher(user=request.user, owner_username=username, code=code) or is_team_student(
            user=request.user, team_id=instance.team_id
        )
        if not authorized:
            message = _("Only course teachers and team members can update or delete a team.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
