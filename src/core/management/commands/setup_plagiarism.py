import time

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tree_sitter import Language


class Command(BaseCommand):
    help = "Compiles supported languages into a usable library for plagiarism detection."

    def handle(self, *args, **options):
        self.stdout.write("Compiling..")
        start_time: float = time.perf_counter()

        Language.build_library(settings.PLAG_COMPILED_LIBRARY, settings.PLAG_SUPPORTED_LANGAUGES)

        end_time: float = time.perf_counter() - start_time
        self.stdout.write(self.style.SUCCESS(f"Successfully compiled libraries in  {end_time:.2}s."))
