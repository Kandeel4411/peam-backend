from django.db import models
from django.conf import settings


class Teacher(models.Model):
    """ Model representing teacher profile. """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="as_teacher")

    def __str__(self) -> str:
        return f"{self.user}"
