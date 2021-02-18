from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from rest_framework import status


def openapi_error_response(description: str, examples: dict) -> openapi.Response:
    """
    Utility function that takes description and examples and constructs an OpenAPI response for swagger
    with django translation utility applied
    """
    return openapi.Response(
        description=_(description),
        examples={"application/json": {key: _(value) for key, value in examples.items()}},
    )
