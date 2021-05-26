from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_flex_fields import is_expanded
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema

from core.utils.openapi import openapi_error_response
from .serializers import ResourcesLocatorRequestSerializer, ResourcesLocatorResponseSerializer
from .resources import ResourcesLocator


class ResourcesLocatorView(APIView):
    """
    Base view for the resource locator.
    """

    @swagger_auto_schema(
        request_body=ResourcesLocatorRequestSerializer(),
        responses={
            status.HTTP_200_OK: ResourcesLocatorResponseSerializer(),
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
        Retrieve a resource url.

        .
        """

        serializer = ResourcesLocatorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        locator = ResourcesLocator()

        model = locator.get_model(resource=(resource := data["resource"]))
        instance = model._default_manager.get(uid=data["uid"])

        response = {"url": locator.get_resolver(resource=resource)(instance=instance)}
        response = ResourcesLocatorResponseSerializer(response).data
        return Response(response, status=status.HTTP_200_OK)
