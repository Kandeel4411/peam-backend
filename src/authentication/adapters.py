from django.contrib.sites.shortcuts import get_current_site
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse, URLPattern
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom allauth account adapter
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Constructs the email confirmation (activation) url.
        """
        site = get_current_site(request)
        location = reverse("account_confirm_email", args=[emailconfirmation.key])

        protocol: str = settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL
        return f"{protocol}://{site.domain}{location}"
