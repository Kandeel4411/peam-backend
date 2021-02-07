import uuid

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import CICharField


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractUser):
    """ Custom Django User """

    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True, verbose_name=_("Profile Picture"))
    username = CICharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    def save(self, *args, **kwargs):
        """
        Custom save method
        """
        self.username = self.username.lower()  # Making sure username is always lowercase
        return super().save(*args, **kwargs)
