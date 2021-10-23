from pathlib import Path
import environ

env = environ.Env()
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent.parent
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR / ".env.local.prod"))

from .base import *  # noqa

DEBUG = env.bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["0.0.0.0", "localhost"])


# django-cors-headers
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env.bool("DJANGO_CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ORIGIN_WHITELIST = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=["https://localhost", "https://127.0.0.1"])

# AUTHENTICATION
# ------------------------------------------------------------------------------
AUTH_USER_MODEL = "users.User"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/api/auth/login"

# dj-rest-auth
# ------------------------------------------------------------------------------
JWT_AUTH_SECURE = env.bool("DJANGO_JWT_AUTH_SECURE", default=True)

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 6

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

# djangorestframework-simplejwt
# ------------------------------------------------------------------------------
SIMPLE_JWT.update(  # noqa
    {
        "ALGORITHM": "RS256",
        "SIGNING_KEY": env("DJANGO_JWT_KEY"),
        "VERIFYING_KEY": env("DJANGO_JWT_VERIFY_KEY"),
    }
)

# django-rest-framework
# -------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTCookieAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# Swagger Settings
# ------------------------------------------------------------------------------
SWAGGER_SETTINGS.update({"SERVE_PUBLIC": env("DJANGO_SWAGGER_SERVE_PUBLIC", default=False)})  # noqa

# DATABASES
# ------------------------------------------------------------------------------
DATABASES = {"default": {**env.db("DATABASE_URL"), "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60)}}

# CACHES
# ------------------------------------------------------------------------------
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True

# STATIC
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="")

if env("DJANGO_EMAIL_BACKEND", default="") != "django.core.mail.backends.console.EmailBackend":
    EMAIL_HOST = env("DJANGO_EMAIL_HOST")
    EMAIL_PORT = env("DJANGO_EMAIL_PORT", default=465)
    EMAIL_USE_SSL = env.bool("DJANGO_EMAIL_USE_SSL", default=True)
    EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=False)
    EMAIL_HOST_USER = env.str("DJANGO_EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env.str("DJANGO_EMAIL_HOST_PASSWORD")

# ADMIN
# ------------------------------------------------------------------------------
ADMIN_URL = env("DJANGO_ADMIN_URL")

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}
