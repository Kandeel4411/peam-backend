"""
With these settings, tests run faster.
"""
from pathlib import Path

from .base import *  # noqa
from .base import env


# GENERAL
# ------------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent.parent
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env.dev"))

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="usNnkJ9v5ZKI3Jkii8OoCFdTjgh2DhfEpJFuSkCb3tikXK8rA0CiqDvmBx7W1Uhb",
)

TEST_RUNNER = "django.test.runner.DiscoverRunner"

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}

# django-rest-framework
# -------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTCookieAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}


# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# PASSWORDS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[-1]["OPTIONS"]["loaders"] = [  # type: ignore[index] # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
