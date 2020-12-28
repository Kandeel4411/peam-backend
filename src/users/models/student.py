from django.db import models
from django.conf import settings


class Student(models.Model):
    """ Model representing student profile. """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="as_student")

    def __str__(self) -> str:
        return f"{self.user}"
