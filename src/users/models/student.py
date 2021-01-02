import uuid

from django.db import models
from django.conf import settings


class Student(models.Model):
    """ Model representing student profile. """

    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE, related_name="as_student"
    )

    def __str__(self) -> str:
        return f"{self.user}"
