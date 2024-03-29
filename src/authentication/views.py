from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import status
from django.utils.decorators import method_decorator
from dj_rest_auth.serializers import LoginSerializer, PasswordChangeSerializer
from dj_rest_auth.views import (
    LoginView,
    PasswordChangeView,
)

from .serializers import LoginResponseSerializer


# TODO: Figure out a better method to redecorate views
LoginView = swagger_auto_schema(
    method="post",
    request_body=LoginSerializer(),
    responses={status.HTTP_200_OK: LoginResponseSerializer()},
)(LoginView.as_view())
