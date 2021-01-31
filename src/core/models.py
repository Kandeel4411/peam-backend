import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings


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
    created_at = models.DateTimeField(default=timezone.now, blank=True, verbose_name=_("Created At"))

    class Meta:
        managed = True
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self) -> str:
        return f"{self.type}: {self.author} to {self.recipient} at {timezone.localtime(self.created_at)}"
