from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, filters
from rest_flex_fields import is_expanded
from drf_yasg.utils import swagger_auto_schema
from dj_rest_auth.serializers import PasswordChangeSerializer
from dj_rest_auth.views import PasswordChangeView

from core.utils.openapi import openapi_error_response
from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from .serializers import UserSerializer, AvatarSerializer, ProfileSerializer

User = get_user_model()

BaseUserPasswordChangeView = swagger_auto_schema(
    method="post",
    request_body=PasswordChangeSerializer(),
    responses={status.HTTP_200_OK: "New password has been saved."},
)(PasswordChangeView.as_view())


class UserView(GenericAPIView):
    """
    Base view for users.
    """

    queryset = User._default_manager.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "name"]

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        List users.

        Search & expansion query params apply*
        """
        instances = self.filter_queryset(self.get_queryset())
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instances, many=True, **config)
        return Response({"users": serializer.data})


class UserDetailView(GenericAPIView):
    """
    Base view for a specific user.
    """

    queryset = User._default_manager.all()
    serializer_class = UserSerializer
    lookup_field = "username"

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        responses={
            status.HTTP_200_OK: UserSerializer(),
            status.HTTP_403_FORBIDDEN: openapi_error_response(
                description="Authorization specific errors", examples={"error": "message"}
            ),
        },
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a user.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)


class BaseUserView(GenericAPIView):
    """
    Base view for the current user.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    @swagger_auto_schema(query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: UserSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves the current user.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(request.user, **config)
        return Response(serializer.data)

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(),
        request_body=UserSerializer(),
        responses={
            status.HTTP_200_OK: UserSerializer(),
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
        Updates the current user.

        Expansion query params apply*
        """
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(request.user, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()

        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ""})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes the current user.

        Removes related objects
        """
        # Only setting user as inactive for now
        request.user.is_active = False

        with transaction.atomic():
            request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseUserAvatarView(GenericAPIView):
    """
    Base view for updating a user's avatar.
    """

    serializer_class = AvatarSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(request_body=AvatarSerializer(), responses={status.HTTP_200_OK: AvatarSerializer()})
    def patch(self, request, *args, **kwargs) -> Response:
        """
        Updates current user's avatar.

        .
        """
        serializer = self.get_serializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save()

        return Response(serializer.data)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ""})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes current user's avatar.

        .
        """
        with transaction.atomic():
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseUserProfileView(GenericAPIView):
    """
    Base view for the current user's profile.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    @swagger_auto_schema(
        query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: ProfileSerializer()}
    )
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves the current user's profile.

        Expansion query params apply*
        """
        queryset = User._default_manager

        if is_expanded(self.request, "courses_taken"):
            queryset = queryset.prefetch_related("courses_taken")
        if is_expanded(self.request, "courses_taught"):
            queryset = queryset.prefetch_related("courses_taught")
        if is_expanded(self.request, "teams"):
            queryset = queryset.prefetch_related("teams")
        if is_expanded(self.request, "courses_owned"):
            queryset = queryset.prefetch_related("courses_owned")

        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(queryset.get(pk=request.user.pk), **config)
        return Response(serializer.data)
