import json

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.views import status, Response
from rest_framework_simplejwt.tokens import AccessToken

from authentication.serializers import CustomTokenObtainPairSerializer
from ..factories.users import UserFactory


User = get_user_model()


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db(transaction=True)
def test_jwt_login_with_username_success(api_client: APIClient):
    """
    Tests for the auth login view
    """

    url: str = reverse("rest_login")

    login_data: dict[str, str] = {"username": "some_user", "password": "password"}
    user: User = UserFactory.create(username=login_data["username"], password=login_data["password"])

    # check that login succeeds
    response: Response = api_client.post(url, data=login_data, format="json")
    assert response.status_code == status.HTTP_200_OK

    access_token: str = json.loads(response.content)["access_token"]
    access_token: AccessToken = AccessToken(token=access_token)

    # check that username is actually the username of the user
    assert access_token["username"] == user.username
