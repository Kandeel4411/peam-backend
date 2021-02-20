import uuid
from typing import Optional

from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail

from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.postgres.fields import CICharField


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project
class User(AbstractBaseUser, PermissionsMixin):
    """ Custom Django User """

    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True, verbose_name=_("Profile Picture"))
    email = models.EmailField(verbose_name=_("Email address"), null=False, blank=False)
    name = models.CharField(_("Name"), max_length=150, blank=True, null=False)

    username_validator = UnicodeUsernameValidator()
    username = CICharField(
        verbose_name=_("Username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    is_staff = models.BooleanField(
        _("Staff Status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. " "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def save(self, *args, **kwargs):
        """
        Custom save method
        """
        self.username = self.username.lower()  # Making sure username is always lowercase
        return super().save(*args, **kwargs)
