from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from core.utils.mixins import MultipleRequiredFieldLookupMixin
from .models import Course, ProjectRequirement, CourseAttachment, ProjectRequirementAttachment
from .serializers import (
    CourseSerializer,
    ProjectRequirementSerializer,
    CourseAttachmentSerializer,
    ProjectRequirementAttachmentSerializer,
)


class CourseView(GenericAPIView):
    """
    Base view for courses.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @swagger_auto_schema(request_body=CourseSerializer(), responses={status.HTTP_201_CREATED: CourseSerializer()})
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CourseDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_fields = ("owner__user__username", "code")
    lookup_url_kwargs = ("owner", "code")

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRequirementDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course project requirement.
    """

    queryset = ProjectRequirement.objects.all()
    serializer_class = ProjectRequirementSerializer
    lookup_fields = ("course__owner__user__username", "course__code", "title")
    lookup_url_kwargs = ("owner", "code", "title")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a project requirement instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific course attachment.
    """

    queryset = CourseAttachment.objects.all()
    serializer_class = CourseAttachmentSerializer
    lookup_fields = ("course__owner__user__username", "course__code", "uid")
    lookup_url_kwargs = ("owner", "code", "uid")

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseAttachmentSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a course attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=CourseAttachmentSerializer(), responses={status.HTTP_201_CREATED: CourseAttachmentSerializer()}
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a course attachment instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={status.HTTP_200_OK: CourseAttachmentSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a course attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: CourseAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a course attachment instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectRequirementAttachmentDetailView(MultipleRequiredFieldLookupMixin, GenericAPIView):
    """
    Base view for a specific project requirement attachment.
    """

    queryset = ProjectRequirementAttachment.objects.all()
    serializer_class = ProjectRequirementAttachmentSerializer
    lookup_fields = (
        "requirement__course__owner__user__username",
        "requirement__course__code",
        "requirement__title",
        "uid",
    )
    lookup_url_kwargs = ("owner", "code", "title", "uid")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a project requirement attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ProjectRequirementAttachmentSerializer(),
        responses={status.HTTP_201_CREATED: ProjectRequirementAttachmentSerializer()},
    )
    def post(self, request, *args, **kwargs) -> Response:
        """
        Create a project requirement attachment instance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ProjectRequirementAttachmentSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Update a project requirement attachment instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ProjectRequirementAttachmentSerializer()})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a project requirement attachment instance.
        """
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
