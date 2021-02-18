import datetime

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from courses.models import CourseInvitation, Course
from .serializers import (
    CourseInvitationSerializer,
    CourseInvitationResponseSerializer,
    CourseInvitationRequestSerializer,
    CourseInvitationStatusRequestSerializer,
)

User = get_user_model()


class CourseInvitationView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course invitations
    """

    queryset = CourseInvitation.objects.all()
    serializer_class = CourseInvitationSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseInvitationSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves course invitation instances.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"invitations": serializer.data})

    @swagger_auto_schema(
        request_body=CourseInvitationRequestSerializer(),
        responses={status.HTTP_200_OK: CourseInvitationResponseSerializer()},
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Send a course invitation.
        """
        request_serializer = CourseInvitationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        emails = request_serializer.validated_data.pop("emails")
        data = request_serializer.validated_data

        # Sending course invite for each email
        success = []
        fail = []
        for email in emails:
            data["email"] = email
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
    Base view for a specific course invitation requirement.
    """

    queryset = CourseInvitation.objects.all()
    serializer_class = CourseInvitationSerializer
    lookup_field = "token"

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseInvitationSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course invitation instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CourseInvitationStatusRequestSerializer(), responses={status.HTTP_201_CREATED: "Success"}
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Acceptance or denial of a course invitation instance.
        """
        instance = self.get_object()
        request_serializer = CourseInvitationStatusRequestSerializer(
            instance=instance, data=request.data, context=self.get_serializer_context()
        )
        request_serializer.is_valid(raise_exception=True)

        invite_status = request_serializer.validated_data["status"]

        # TODO remove manual updating for serializer instead
        with transaction.atomic():
            instance.status = invite_status
            if status == CourseInvitation.ACCEPTED:
                if instance.type == CourseInvitation.TEACHER_INVITE:
                    instance.course.teachers.add(request.user)
                elif instance.type == CourseInvitation.STUDENT_INVITE:
                    instance.course.students.add(request.user)
            instance.save()

        return Response(status=status.HTTP_201_CREATED)
