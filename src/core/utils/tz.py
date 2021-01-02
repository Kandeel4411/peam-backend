import datetime

from django.utils import timezone


def local_timezone_now() -> datetime.datetime:
    """Helper function that returns timezone.now with respect to the set timezone"""
    return timezone.localtime(timezone.now())
