import uuid

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    """ Custom Django User """

    TEACHER = "Teacher"
    STUDENT = "Student"
    ANON = "Anon"
    USER_ROLE_CHOICES = (
        (
            TEACHER,
            TEACHER,
        ),
        (
            STUDENT,
            STUDENT,
        ),
    )

    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True, verbose_name=_("Profile Picture"))
