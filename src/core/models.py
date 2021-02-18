import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from .utils.invitation import generate_token


class Notification(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.DO_NOTHING, related_name="notifications_sent"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.DO_NOTHING, related_name="notifications_received"
    )
    author_name = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Author Name"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    link = models.URLField(blank=True, null=False, verbose_name=_("Link"))
    type = models.CharField(max_length=20, blank=False, null=False, verbose_name=_("Type"))
    unread = models.BooleanField(default=False, null=False, blank=True, verbose_name=_("Unread"))
    created_at = models.DateTimeField(
        default=timezone.now, blank=True, null=False, editable=False, verbose_name=_("Created At")
    )

    class Meta:
        managed = True
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self) -> str:
        return f"{self.type}: {self.author} to {self.recipient} at {timezone.localtime(self.created_at)}"


class BaseInvitation(models.Model):
    PENDING: str = "Pending"
    ACCEPTED: str = "Accepted"
    REJECTED: str = "Rejected"
    EXPIRED: str = "Expired"

    STATUS_CHOICES: tuple = (
        (PENDING, PENDING),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
        (EXPIRED, EXPIRED),
    )

    token = models.CharField(max_length=64, unique=True, default=generate_token)
    status = models.CharField(choices=STATUS_CHOICES, max_length=30, default=PENDING, null=False)
    expiry_date = models.DateTimeField(verbose_name=_("Expiry Date"), null=False, blank=False)
    created_at = models.DateTimeField(
        default=timezone.now, blank=True, null=False, editable=False, verbose_name=_("Created At")
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        to_field="uid",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(created_at__lte=models.F("expiry_date")),
                name="%(class)s_expiry_date_constraint",
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Custom save method
        """
        if self.invitation_expired(save=False):
            self.status = self.EXPIRED
        return super().save(*args, **kwargs)

    def invitation_expired(self, save=False) -> bool:
        """
        Helper function that checks if the invitation has already expired the set expiry_date

        :save: will update instance status if it was expired
        """
        if self.expiry_date <= timezone.now():
            if save and self.status == self.EXPIRED:
                self.status = self.EXPIRED
                self.save()
            return True
        return False

    @classmethod
    def send_invitation(
        cls, request, email_template_prefix="invitations/email_invite", *args, **kwargs
    ) -> "BaseInvitation":
        """
        Helper method that wraps creation of a invitation and sends an email and
        returns created invitation instance if successful.

        :request: django http request

        :email_template: template that is going to be used for
        the invitation(site_name, email, invite_url, sender and expiry_date are available by default in ctx)

        :*args, **kwargs: arguments that are going to be directly passed to ORM object creation

        *Note:* This method should generally be used instead of manual creation of invitation as
        it ensures that if creation fails, an email wont be sent and vice versa
        """
        raise NotImplementedError("This method must be implemented by subclasses")
