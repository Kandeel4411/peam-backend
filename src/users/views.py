from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, filters
from rest_flex_fields import is_expanded
from drf_yasg.utils import swagger_auto_schema

from core.utils.openapi import openapi_error_response
from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from .serializers import UserSerializer
from .permissions import UserDetailViewPermission

User = get_user_model()


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

    permission_classes = (*GenericAPIView.permission_classes, UserDetailViewPermission)
    queryset = User._default_manager.all()
    serializer_class = UserSerializer
    lookup_field = "username"

    @swagger_auto_schema(query_serializer=FlexFieldsQuerySerializer(), responses={status.HTTP_200_OK: UserSerializer()})
    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieves a user.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, **config)
        return Response(serializer.data)

    @transaction.atomic
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
        Updates a user.

        Expansion query params apply*
        """
        instance = self.get_object()
        config = get_flex_serializer_config(request)
        serializer = self.get_serializer(instance, data=request.data, partial=True, **config)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @transaction.atomic
    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ""})
    def delete(self, request, *args, **kwargs) -> Response:
        """
        Deletes a user.

        Removes related objects
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()  # Only setting user as inactive for now
        return Response(status=status.HTTP_204_NO_CONTENT)
