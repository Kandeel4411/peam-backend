import json

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.views import status, Response
from rest_framework_simplejwt.tokens import AccessToken

from users.models import Teacher, Student
from users.tests.factories import UserFactory, StudentFactory, TeacherFactory
from core.auth.serializers import CustomTokenObtainPairSerializer


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

    # User that is neither a student or a teacher
    login_data: dict[str, str] = {"username": "some_user", "password": "password"}
    user: User = UserFactory.create(username=login_data["username"], password=login_data["password"])

    response: Response = api_client.post(url, data=login_data, format="json")
    assert response.status_code == status.HTTP_200_OK

    access_token: str = json.loads(response.content)["access_token"]
    access_token: AccessToken = AccessToken(token=access_token)

    assert access_token["role"] == User.ANON

    # User is a teacher
    login_data["username"] = "teacher_user"
    teacher: Teacher = TeacherFactory.create(
        user__username=login_data["username"], user__password=login_data["password"]
    )
    response: Response = api_client.post(url, data=login_data, format="json")
    assert response.status_code == status.HTTP_200_OK

    access_token: str = json.loads(response.content)["access_token"]
    access_token: AccessToken = AccessToken(token=access_token)

    assert access_token["role"] == User.TEACHER

    # User is a student
    login_data["username"] = "student_user"
    student: Student = StudentFactory.create(
        user__username=login_data["username"], user__password=login_data["password"]
    )
    response: Response = api_client.post(url, data=login_data, format="json")
    assert response.status_code == status.HTTP_200_OK

    access_token: str = json.loads(response.content)["access_token"]
    access_token: AccessToken = AccessToken(token=access_token)

    assert access_token["role"] == User.STUDENT
