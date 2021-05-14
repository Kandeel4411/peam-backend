import datetime

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_flex_fields import is_expanded

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from core.utils.openapi import openapi_error_response
from core.constants import InvitationStatus
from courses.models import CourseInvitation, Course, TeamInvitation, Team, TeamStudent
from courses.utils import is_course_student, is_course_teacher, is_course_owner, is_team_student
from .serializers import (
    CourseInvitationSerializer,
    CourseInvitationResponseSerializer,
    CourseInvitationRequestSerializer,
    CourseInvitationStatusRequestSerializer,
    TeamInvitationSerializer,
    TeamInvitationResponseSerializer,
    TeamInvitationRequestSerializer,
    TeamInvitationStatusRequestSerializer,
)


class CourseInvitationView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course invitations
    """

    queryset = CourseInvitation._default_manager.all()
    serializer_class = CourseInvitationSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "sender"):
            queryset = queryset.select_related("sender")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseInvitationSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List course invitations.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course teachers can view the course invitations
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only teachers can view the course invitations.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instances = self.get_queryset()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"invitations": serializer.data})

    @swagger_auto_schema(
        request_body=CourseInvitationRequestSerializer(),
        responses={
            status.HTTP_200_OK: CourseInvitationResponseSerializer(),
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
        Send a course invitation.

        Always returns 200
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]

        # Only course teachers can send a course invitation
        authorized = is_course_teacher(user=request.user, code=code, owner_username=username)
        if not authorized:
            message = _("Only course teachers can send a course invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        request_serializer = CourseInvitationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        emails = request_serializer.validated_data.pop("emails")
        data = request_serializer.validated_data

        # Sending course invite for each email
        success = []
        fail = []
        for email in emails:
            data["email"] = email
            data["status"] = InvitationStatus.PENDING
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=False):
                serializer.save()
                success.append(email)
            else:
                fail.append(
                    {
                        "email": email,
                        # Retrieving serializer error to display
                        "error": list(serializer.errors.values())[0],
                    }
                )

        return Response({"success": success, "fail": fail}, status=status.HTTP_200_OK)


class CourseInvitationDetailView(GenericAPIView):
    """
    Base view for a specific course invitation.
    """

    queryset = CourseInvitation._default_manager.all()
    serializer_class = CourseInvitationSerializer
    lookup_field = "token"

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "sender"):
            queryset = queryset.select_related("sender")
        if is_expanded(self.request, "course"):
            queryset = queryset.select_related("course")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: CourseInvitationSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course invitation.

        expansion query params apply*
        """
        instance = self.get_object()

        # Only course teachers can can view a course invitation
        authorized = is_course_teacher(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only course teachers can view a course invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

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
        Deletes a course invitation.

        Only the course owner can delete the course invitation.
        """
        instance = self.get_object()

        # Only the course owner can delete a course invitation
        authorized = is_course_owner(user=request.user, course_id=instance.course_id)
        if not authorized:
            message = _("Only the course owner can delete a course invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=CourseInvitationStatusRequestSerializer(),
        responses={
            status.HTTP_200_OK: "",
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
        User response to a course invitation.

        Acceptance or denial of a course invitation.
        """
        instance = self.get_object()

        # Only the user the invitation belongs to can accept or decline.
        authorized = request.user.email == instance.email
        if not authorized:
            message = _("Only the user the invitation belongs to can accept or decline.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        request_serializer = CourseInvitationStatusRequestSerializer(
            data=request.data,
        )
        request_serializer.is_valid(raise_exception=True)

        serializer = self.get_serializer(instance=instance, data=request_serializer.validated_data)

        with transaction.atomic():
            serializer.save()

        return Response(status=status.HTTP_200_OK)


class TeamInvitationView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for team invitations
    """

    queryset = TeamInvitation._default_manager.all()
    serializer_class = TeamInvitationSerializer
    lookup_fields = {
        "course_owner": "team__requirement__course__owner__username",
        "course_code": "team__requirement__course__code",
        "requirement_title": "team__requirement__title",
    }

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "sender"):
            queryset = queryset.select_related("sender")
        if is_expanded(self.request, "team"):
            queryset = queryset.select_related("team")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: TeamInvitationSerializer(many=True),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List team invitations.

        Expansion query params apply*
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]
        title: str = kwargs["requirement_title"]

        # Only team members can view the team invitations
        authorized = is_team_student(user=request.user, owner_username=username, code=code, requirement_title=title)
        if not authorized:
            message = _("Only team members can view the team invitations")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instances = self.get_queryset()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"invitations": serializer.data})

    @swagger_auto_schema(
        request_body=TeamInvitationRequestSerializer(),
        responses={
            status.HTTP_200_OK: TeamInvitationResponseSerializer(),
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
        Send a team invitation.

        Always returns 200
        """
        code: str = kwargs["course_code"]
        username: str = kwargs["course_owner"]
        title: str = kwargs["requirement_title"]

        # Only team members can send a team invitation
        authorized = is_team_student(user=request.user, owner_username=username, code=code, requirement_title=title)
        if not authorized:
            message = _("Only team members can send a team invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        request_serializer = TeamInvitationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        emails = request_serializer.validated_data.pop("emails")
        data = request_serializer.validated_data

        # Sending team invite for each email
        success = []
        fail = []
        for email in emails:
            data["email"] = email
            data["status"] = InvitationStatus.PENDING
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=False):
                serializer.save()
                success.append(email)
            else:
                fail.append(
                    {
                        "email": email,
                        # Retrieving serializer error to display
                        "error": list(serializer.errors.values())[0],
                    }
                )

        return Response({"success": success, "fail": fail}, status=status.HTTP_200_OK)


class TeamInvitationDetailView(GenericAPIView):
    """
    Base view for a specific team invitation.
    """

    queryset = TeamInvitation._default_manager.all()
    serializer_class = TeamInvitationSerializer
    lookup_field = "token"

    def get_queryset(self):
        """
        Custom get_queryset
        """
        queryset = super().get_queryset()

        if is_expanded(self.request, "sender"):
            queryset = queryset.select_related("sender")
        if is_expanded(self.request, "team"):
            queryset = queryset.select_related("team")

        return queryset

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: TeamInvitationSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a team invitation.

        Expansion query params apply*
        """
        instance = self.get_object()

        # Only team members can view a team invitation
        authorized = is_team_student(user=request.user, team_id=instance.team_id)
        if not authorized:
            message = _("Only team members can view a team invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

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
        Deletes a team invitation.

        Only a team member can delete the invitation.
        """
        instance = self.get_object()

        # Only team members can delete a team invitation
        authorized = is_team_student(user=request.user, team_id=instance.team_id)
        if not authorized:
            message = _("Only team members can delete a team invitation.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=TeamInvitationStatusRequestSerializer(),
        responses={
            status.HTTP_200_OK: "",
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
        User response to a team invitation.

        Acceptance or denial of a team invitation instance.
        """
        instance = self.get_object()

        # Only the user the invitation belongs to can accept or decline.
        authorized = request.user.email == instance.email
        if not authorized:
            message = _("Only the user the invitation belongs to can accept or decline.")
            return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)

        request_serializer = TeamInvitationStatusRequestSerializer(
            data=request.data,
        )
        request_serializer.is_valid(raise_exception=True)

        serializer = self.get_serializer(instance=instance, data=request_serializer.validated_data)

        with transaction.atomic():
            serializer.save()

        return Response(status=status.HTTP_200_OK)
