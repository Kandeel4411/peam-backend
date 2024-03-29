import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from ..utils.invitations import generate_token
from ..constants import InvitationStatus


class BaseInvitation(models.Model):
    """
    Abstract base model that represents the basic invitation model requirements.
    """

    token = models.CharField(max_length=64, unique=True, default=generate_token)
    status = models.CharField(
        choices=InvitationStatus.STATUS_CHOICES, max_length=30, default=InvitationStatus.PENDING, null=False
    )
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
            # Expiry date must be greater than created_at constraint
            models.CheckConstraint(
                check=models.Q(created_at__lte=models.F("expiry_date")),
                name="%(class)s_expiry_date_constraint",
            ),
            # Status must be one of the defined statuses in InvitationStatus constraint
            models.CheckConstraint(
                check=models.Q(status__in=InvitationStatus.STATUS_LIST),
                name="%(class)s_status_constraint",
            ),
        ]

    def clean(self) -> None:
        """
        Model level validation hook
        """
        if self.pk is not None:  # An update
            # Status is already accepted
            if self.status == InvitationStatus.ACCEPTED:
                raise ValidationError({"status": _("Invitation is already accepted.")})

            # Status is already rejected
            elif self.status == InvitationStatus.REJECTED:
                raise ValidationError({"status": _("Invitation is already rejected.")})

            # Status is already expired
            elif self.invitation_expired(save=True):
                raise ValidationError({"expiry_date": _("Invitation is already expired.")})

        # Expiry date can't be less than the creation date
        if self.expiry_date and self.expiry_date <= self.created_at:
            raise ValidationError({"expiry_date": _("Expiry date can't be less than the creation date.")})

    def save(self, *args, **kwargs) -> None:
        """
        Custom save method
        """
        if self.invitation_expired(save=False):
            self.status = InvitationStatus.EXPIRED
        return super().save(*args, **kwargs)

    def invitation_expired(self, save=False) -> bool:
        """
        Helper function that checks if the invitation has already expired the set expiry_date

        :save: will update instance status if it was expired
        """
        if self.expiry_date <= timezone.now():
            if save and self.status == InvitationStatus.EXPIRED:
                self.status = InvitationStatus.EXPIRED
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

        :*args, **kwargs: arguments that are going to be directly passed to default manager object creation
        method.

        *Note:* This method should generally be used instead of manual creation of invitation as
        it ensures that if creation fails, an email wont be sent and vice versa
        """
        raise NotImplementedError("This method must be implemented by subclasses")
