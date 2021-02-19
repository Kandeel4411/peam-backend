from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_flex_fields import is_expanded
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from core.utils.openapi import openapi_error_response
from .models import (
    Course,
    CourseStudent,
    CourseTeacher,
    Team,
    ProjectRequirement,
    CourseAttachment,
    ProjectRequirementAttachment,
)
from .serializers import (
    CourseSerializer,
    ProjectRequirementSerializer,
    CourseAttachmentSerializer,
    CourseStudentSerializer,
    CourseTeacherSerializer,
    TeamSerializer,
    ProjectRequirementAttachmentSerializer,
)


class CourseView(GenericAPIView):
    """
    Base view for courses.
    """

    queryset = Course._default_manager.all()
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "students"):
            queryset = queryset.prefetch_related("students")
        if is_expanded(self.request, "teachers"):
            queryset = queryset.prefetch_related("teachers")
        if is_expanded(self.request, "requirements"):
            queryset = queryset.prefetch_related("requirements")
            # If expanding requirements as well
            if is_expanded(self.request, "requirements.teams"):
                queryset = queryset.prefetch_related("requirement__teams")
            if is_expanded(self.request, "requirements.attachments"):
                queryset = queryset.prefetch_related("requirement__attachments")
        if is_expanded(self.request, "attachments"):
            queryset = queryset.prefetch_related("attachments")

        # Since we are always retrieving owner object
        queryset.select_related("owner")

        return queryset

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=CourseSerializer(),
        responses={
            status.HTTP_201_CREATED: CourseSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: CourseSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List courses.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"courses": serializer.data})


class CourseDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course.
    """

    queryset = Course._default_manager.all()
    serializer_class = CourseSerializer
    lookup_fields = {
        "course_owner": {"filter_kwarg": "owner__username", "pk": True},
        "course_code": {"filter_kwarg": "code", "pk": True},
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "students"):
            queryset = queryset.prefetch_related("students")
        if is_expanded(self.request, "teachers"):
            queryset = queryset.prefetch_related("teachers")
        if is_expanded(self.request, "requirements"):
            queryset = queryset.prefetch_related("requirements")
            # If expanding requirements as well
            if is_expanded(self.request, "requirements.teams"):
                queryset = queryset.prefetch_related("requirement__teams")
            if is_expanded(self.request, "requirements.attachments"):
                queryset = queryset.prefetch_related("requirement__attachments")
        if is_expanded(self.request, "attachments"):
            queryset = queryset.prefetch_related("attachments")

        # Since we are always retrieving owner object
        queryset.select_related("owner")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: CourseSerializer()}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=CourseSerializer(),
        responses={
            status.HTTP_200_OK: CourseSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a course.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course.

        Removes related objects
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseStudentView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course students.
    """

    queryset = CourseStudent._default_manager.all()
    serializer_class = CourseStudentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "student"):
            queryset = queryset.select_related("student")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: CourseStudentSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course students.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"students": serializer.data})


class CourseTeacherView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course teacher.
    """

    queryset = CourseTeacher._default_manager.all()
    serializer_class = CourseTeacherSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "teacher"):
            queryset = queryset.select_related("teacher")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: CourseTeacherSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course teachers.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"teachers": serializer.data})


class ProjectRequirementView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for project requirements.
    """

    queryset = ProjectRequirement._default_manager.all()
    serializer_class = ProjectRequirementSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "teams"):
            queryset = queryset.prefetch_related("teams")
        if is_expanded(self.request, "attachments"):
            queryset = queryset.prefetch_related("attachments")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={status.HTTP_200_OK: ProjectRequirementSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List project requirements.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"requirements": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectRequirementSerializer(),
        responses={
            status.HTTP_201_CREATED: ProjectRequirementSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectRequirementDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project requirement.
    """

    queryset = ProjectRequirement._default_manager.all()
    serializer_class = ProjectRequirementSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "requirement_title": {"filter_kwarg": "title", "pk": True},
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        # Optimizing queries
        if is_expanded(self.request, "teams"):
            queryset = queryset.prefetch_related("teams")
        if is_expanded(self.request, "attachments"):
            queryset = queryset.prefetch_related("attachments")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: ProjectRequirementSerializer()}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectRequirementSerializer(),
        responses={
            status.HTTP_200_OK: ProjectRequirementSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a project requirement.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement.

        Removes related objects
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for teams.
    """

    queryset = Team._default_manager.all()
    serializer_class = TeamSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "students"):
            queryset = queryset.prefetch_related("students")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: TeamSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List teams.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"teams": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=TeamSerializer(),
        responses={
            status.HTTP_201_CREATED: TeamSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a team.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific team.
    """

    queryset = Team._default_manager.all()
    serializer_class = TeamSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
        "team_name": {"filter_kwarg": "name", "pk": True},
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "students"):
            queryset = queryset.prefetch_related("students")

        return queryset

    @swagger_auto_schema(query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: TeamSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a team.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=TeamSerializer(),
        responses={
            status.HTTP_201_CREATED: TeamSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a team.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: TeamSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a team.

        Removes related objects
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseAttachmentView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course attachments.
    """

    queryset = CourseAttachment._default_manager.all()
    serializer_class = CourseAttachmentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={status.HTTP_200_OK: CourseAttachmentSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course attachments.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"attachments": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=CourseAttachmentSerializer(),
        responses={
            status.HTTP_201_CREATED: CourseAttachmentSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course attachment.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course attachment.
    """

    queryset = CourseAttachment._default_manager.all()
    serializer_class = CourseAttachmentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "attachment_uid": {"filter_kwarg": "uid", "pk": True},
    }

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: CourseAttachmentSerializer()}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course attachment.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=CourseAttachmentSerializer(),
        responses={
            status.HTTP_201_CREATED: CourseAttachmentSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a course attachment.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course attachment.

        Removes related objects
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRequirementAttachmentView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for project requirement attachments.
    """

    queryset = ProjectRequirementAttachment._default_manager.all()
    serializer_class = ProjectRequirementAttachmentSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
    }

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List project requirement attachments.

        Expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"attachments": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectRequirementAttachmentSerializer(),
        responses={
            status.HTTP_201_CREATED: ProjectRequirementAttachmentSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement attachment.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectRequirementAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project requirement attachment.
    """

    queryset = ProjectRequirementAttachment._default_manager.all()
    serializer_class = ProjectRequirementAttachmentSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
        "attachment_uid": {"filter_kwarg": "uid", "pk": True},
    }

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer()},
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement attachment.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=ProjectRequirementAttachmentSerializer(),
        responses={
            status.HTTP_200_OK: ProjectRequirementAttachmentSerializer(),
            status.HTTP_400_BAD_REQUEST: openapi_error_response(
                description="Resource specific errors.",
                examples={
                    "property": "error message.",
                },
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a project requirement attachment.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement attachment.

        Removes related objects
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
