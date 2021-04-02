from allauth.account.models import EmailAddress
from django.contrib import admin


class EmailAddressInline(admin.TabularInline):
    """
    A class for inlining email-addresses
    """

    model = EmailAddress
    extra = 0
