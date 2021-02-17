from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from .models import Course, CourseStudent, Team, ProjectRequirement, CourseAttachment, ProjectRequirementAttachment
from .serializers import (
    CourseSerializer,
    ProjectRequirementSerializer,
    CourseAttachmentSerializer,
    TeamSerializer,
    ProjectRequirementAttachmentSerializer,
)


class CourseView(GenericAPIView):
    """
    Base view for courses.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @transaction.atomic
    @swagger_auto_schema(request_body=CourseSerializer(), responses={status.HTTP_201_CREATED: CourseSerializer()})
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves course instances.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"courses": serializer.data})


class CourseDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_fields = {
        "course_owner": {"filter_kwarg": "owner__username", "pk": True},
        "course_code": {"filter_kwarg": "code", "pk": True},
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(request_body=CourseSerializer(), responses={status.HTTP_200_OK: CourseSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates a course instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRequirementView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for project requirements.
    """

    queryset = ProjectRequirement.objects.all()
    serializer_class = ProjectRequirementSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves project requirement instances.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"requirements": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        request_body=ProjectRequirementSerializer(), responses={status.HTTP_201_CREATED: ProjectRequirementSerializer()}
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectRequirementDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project requirement.
    """

    queryset = ProjectRequirement.objects.all()
    serializer_class = ProjectRequirementSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "requirement_title": {"filter_kwarg": "title", "pk": True},
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        request_body=ProjectRequirementSerializer(), responses={status.HTTP_200_OK: ProjectRequirementSerializer()}
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a project requirement instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for teams.
    """

    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: TeamSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves team instances.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"teams": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(request_body=TeamSerializer(), responses={status.HTTP_201_CREATED: TeamSerializer()})
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a team instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TeamDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific team.
    """

    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
        "team_name": {"filter_kwarg": "name", "pk": True},
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: TeamSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a team instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(request_body=TeamSerializer(), responses={status.HTTP_201_CREATED: TeamSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a team instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: TeamSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a team instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseAttachmentView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for course attachments.
    """

    queryset = CourseAttachment.objects.all()
    serializer_class = CourseAttachmentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseAttachmentSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves course attachments.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"attachments": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        request_body=CourseAttachmentSerializer(), responses={status.HTTP_201_CREATED: CourseAttachmentSerializer()}
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course attachment.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course attachment.
    """

    queryset = CourseAttachment.objects.all()
    serializer_class = CourseAttachmentSerializer
    lookup_fields = {
        "course_owner": "course__owner__username",
        "course_code": "course__code",
        "attachment_uid": {"filter_kwarg": "uid", "pk": True},
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseAttachmentSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        request_body=CourseAttachmentSerializer(), responses={status.HTTP_201_CREATED: CourseAttachmentSerializer()}
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a course attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course attachment instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRequirementAttachmentView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for project requirement attachments.
    """

    queryset = ProjectRequirementAttachment.objects.all()
    serializer_class = ProjectRequirementAttachmentSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer(many=True)})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves project requirement attachments.
        """
        instances = self.get_queryset()
        serializer = self.get_serializer(instances, many=True)
        return Response({"attachments": serializer.data})

    @transaction.atomic
    @swagger_auto_schema(
        request_body=ProjectRequirementAttachmentSerializer(),
        responses={status.HTTP_201_CREATED: ProjectRequirementAttachmentSerializer()},
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement attachment.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectRequirementAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project requirement attachment.
    """

    queryset = ProjectRequirementAttachment.objects.all()
    serializer_class = ProjectRequirementAttachmentSerializer
    lookup_fields = {
        "course_owner": "requirement__course__owner__username",
        "course_code": "requirement__course__code",
        "requirement_title": "requirement__title",
        "attachment_uid": {"filter_kwarg": "uid", "pk": True},
    }

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(
        request_body=ProjectRequirementAttachmentSerializer(),
        responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer()},
    )
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a project requirement attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement attachment instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
