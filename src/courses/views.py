from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_flex_fields import is_expanded
from django.db import transaction
from django.utils.translation import gettext_lazy as _
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
    TeamStudentSerializer,
    ProjectRequirementAttachmentSerializer,
)
from .utils import is_course_student, is_course_teacher, is_course_owner, is_team_student


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
        course = serializer.save()

        #  Link current course owner/request user as course teacher
        data = {"teacher": course.owner_id, "course": course.uid}
        course_teacher_serializer = CourseTeacherSerializer(data=data)
        course_teacher_serializer.is_valid(raise_exception=True)
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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.uid) or is_course_student(
            user=request.user, course_id=instance.uid
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a course.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers can update
        authorized = is_course_teacher(user=request.user, course_id=instance.uid)
        if not authorized:
            message = _("Only course teachers can update.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        # Only course owner can transfer ownership
        elif "owner" in request.data and not is_course_owner(user=request.user, course_id=instance.uid):
            message = _("Only the course owner can transfer ownership.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a course.

        Removes related objects
        """
        instance = self.get_object()

        # Only the course owner can delete
        authorized = is_course_owner(user=request.user, course_id=instance.uid)
        if not authorized:
            message = _("Only the course owner can delete.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseStudentSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course students.

        Expansion query params apply*
        """

        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"students": serializer.data})


class CourseStudentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course student.
    """

    queryset = CourseStudent._default_manager.all()
    serializer_class = CourseStudentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "course_student": {"filter_kwarg": "student__username", "pk": True},
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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseStudentSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course student.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id) or is_course_student(
            user=request.user, course_id=instance.course_id
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a course student.

        Removes related objects
        """
        instance = self.get_object()

        # Only course teachers can delete
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only the course teachers can remove a student.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseTeacherSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course teachers.

        Expansion query params apply*
        """

        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"teachers": serializer.data})


class CourseTeacherDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course teacher.
    """

    queryset = CourseTeacher._default_manager.all()
    serializer_class = CourseTeacherSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "course_teacher": {"filter_kwarg": "teacher__username", "pk": True},
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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseStudentSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course teacher.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id) or is_course_student(
            user=request.user, course_id=instance.course_id
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a course teacher.

        Removes related objects
        """
        instance = self.get_object()

        # Only the course owner can delete
        authorized = is_course_owner(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only the course owner can remove a teacher.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        responses={
            status.HTTP_200_OK: ProjectRequirementSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List project requirements.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course teachers can create a project requirement
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only course teachers can create a project requirement.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: ProjectRequirementSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id) or is_course_student(
            user=request.user, course_id=instance.course_id
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a project requirement.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers can update a requirement
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete project requirement.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a project requirement.

        Removes related objects
        """
        instance = self.get_object()

        # Only course teachers can update a requirement
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete project requirement.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: TeamSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List teams.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a team.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course students can create a team
        authorized = is_course_student(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only course students can create a team.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(data=request.data, **config)
        serializer.is_valid(raise_exception=True)
        team = serializer.save()

        #  Link current request user as team student
        data = {"student": request.user.uid, "team": team.uid}
        team_student_serializer = TeamStudentSerializer(data=data)
        team_student_serializer.is_valid(raise_exception=True)
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

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: TeamSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a team.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(
            user=request.user, course_id=instance.requirement.course_id
        ) or is_course_student(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a team.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers and team members can update or delete a team
        authorized = is_course_teacher(user=request.user, course_id=instance.requirement.course_id) or is_team_student(
            user=request.user, team_id=instance.uid
        )
        if not authorized:
            message = _("Only course teachers and team members can update or delete a team.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a team.

        Removes related objects
        """
        instance = self.get_object()

        # Only course teachers and team members can update or delete a team
        authorized = is_course_teacher(user=request.user, course_id=instance.requirement.course_id) or is_team_student(
            user=request.user, team_id=instance.uid
        )
        if not authorized:
            message = _("Only course teachers and team members can update or delete a team.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        responses={
            status.HTTP_200_OK: CourseAttachmentSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course attachments.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course attachment.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course teachers can create a course attachment
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only course teachers can create a course attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseAttachmentSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course attachment.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id) or is_course_student(
            user=request.user, course_id=instance.course_id
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a course attachment.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers can update or delete a course attachment
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete course attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a course attachment.

        Removes related objects
        """
        instance = self.get_object()

        # Only course teachers can update or delete a course attachment
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete course attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        responses={
            status.HTTP_200_OK: ProjectRequirementAttachmentSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List project requirement attachments.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
            user=request.user, code=code, owner_username=username
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement attachment.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course teachers can create a project requirement attachment
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only course teachers can create a project requirement attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
        responses={
            status.HTTP_200_OK: ProjectRequirementAttachmentSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement attachment.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only those who belong to the course can retrieve
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id) or is_course_student(
            user=request.user, course_id=instance.course_id
        )
        if not authorized:
            message = _("User must be either a student or a teacher of the course.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

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
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a project requirement attachment.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers can update or delete a project requirement attachment
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete project requirement attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
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
        Deletes a project requirement attachment.

        Removes related objects
        """
        instance = self.get_object()

        # Only course teachers can update or delete a project requirement attachment
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can a update or delete project requirement attachment.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
