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
AUTHENTICATION_BACKENDS = [
    # allauth specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
    # Needed to login by username in Django admin, regardless of allauth
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "users.User"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/api/auth/login"

# dj-rest-auth
# ------------------------------------------------------------------------------
REST_USE_JWT = True
REST_SESSION_LOGIN = False
JWT_AUTH_COOKIE = "jwt-auth"
JWT_AUTH_SECURE = False
JWT_AUTH_HTTPONLY = True
JWT_AUTH_SAMESITE = "Lax"

REST_AUTH_SERIALIZERS = {
    "JWT_TOKEN_CLAIMS_SERIALIZER": "core.auth.serializers.CustomTokenObtainPairSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {"REGISTER_SERIALIZER": "core.auth.serializers.CustomRegisterSerializer"}

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 8
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_AUTHENTICATION_METHOD = "username_email"

ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = None
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True

ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_MAX_EMAIL_ADDRESSES = 1  # User wont be able to change his email

ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False

ACCOUNT_PRESERVE_USERNAME_CASING = True

# djangorestframework-simplejwt
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_KEY", default=SECRET_KEY),
    "AUTH_HEARDER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "AUDIENCE": None,
    "ISSUER": None,
    "USER_ID_FIELD": "uid",
    "USER_ID_CLAIM": "user_id",
    "JTI_CLAIM": "jwt_id",
    "TOKEN_TYPE_CLAIM": "jwt_type",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# django-rest-framework
# -------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTCookieAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
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
