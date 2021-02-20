from pathlib import Path
from datetime import timedelta

from .base import *  # noqa
from .base import env

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent.parent
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env.dev"))

DEBUG = True
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="6PYoIucrBDY9VRXvcVQNkaBs1SONtVXSnyrTIs949YthW18tjBCjXwUfycItgY0F",
)
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# django-cors-headers
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# AUTHENTICATION
# ------------------------------------------------------------------------------

# dj-rest-auth
# ------------------------------------------------------------------------------

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 8

# djangorestframework-simplejwt
# ------------------------------------------------------------------------------
SIMPLE_JWT.update(  # noqa
    {
        "SIGNING_KEY": env("JWT_KEY", default=SECRET_KEY),
    }
)

# django-rest-framework
# -------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTCookieAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]  # noqa F405
