from django.contrib.auth import get_user_model
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status, filters
from rest_flex_fields import is_expanded
from drf_yasg.utils import swagger_auto_schema


from core.utils.flex_fields import get_flex_serializer_config, FlexFieldsQuerySerializer
from .serializers import UserSerializer


User = get_user_model()


class UserView(GenericAPIView):
    """
    Base view for users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]

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
