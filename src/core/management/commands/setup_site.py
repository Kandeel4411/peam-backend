from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = "Sets the site domain name and site display name"

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        site.domain = settings.SITE_DOMAIN
        site.name = settings.SITE_DISPLAY
        site.save()
        Site.objects.clear_cache()
