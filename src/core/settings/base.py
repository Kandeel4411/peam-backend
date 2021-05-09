"""
Base settings to build other settings files upon.
"""
from pathlib import Path
from datetime import timedelta

import environ

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent.parent
APPS_DIR = ROOT_DIR / "src"
env = environ.Env()


DEBUG = env.bool("DJANGO_DEBUG", False)

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = [str(ROOT_DIR / "locale")]


ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "grappelli",  # Third-party - must be installed before django.contrib.admin
    "django.contrib.admin",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "drf_yasg",
]

LOCAL_APPS = [
    "users.apps.UsersConfig",
    "courses.apps.CoursesConfig",
    "core.apps.CoreConfig",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


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


# PEAM BACKEND
# ------------------------------------------------------------------------------

# django path url patterns
FRONTEND_EMAIL_CONFIRMATION_URL = "signup/email/verify/<str:key>/"
FRONTEND_PASSWORD_RESET_CONFIRMATION_URL = "password/reset/confirm/<slug:uidb64>/<slug:token>/"
FRONTEND_LOGIN_URL = "login/"
FRONTEND_COURSE_INVITATION_PARAM = "course-invitation"
FRONTEND_TEAM_INVITATION_PARAM = "team-invitation"

# plagiarism detection - tree-sitter
PLAG_SUPPORTED_LANGAUGES = ["src/plagiarism/vendor/tree-sitter-javascript", "src/plagiarism/vendor/tree-sitter-python"]
PLAG_COMPILED_LIBRARY = "src/plagiarism/build/languages.so"

# drf-flex-fields
# ------------------------------------------------------------------------------
REST_FLEX_FIELDS = {"EXPAND_PARAM": "expand", "OMIT_PARAM": "omit", "FIELDS_PARAM": "only"}


# dj-rest-auth
# ------------------------------------------------------------------------------
REST_USE_JWT = True
REST_SESSION_LOGIN = False
JWT_AUTH_COOKIE = "jwt-auth"
JWT_AUTH_SECURE = False
JWT_AUTH_HTTPONLY = True
JWT_AUTH_SAMESITE = "Lax"
OLD_PASSWORD_FIELD_ENABLED = True

REST_AUTH_SERIALIZERS = {
    "JWT_TOKEN_CLAIMS_SERIALIZER": "core.auth.serializers.CustomTokenObtainPairSerializer",
    "USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer",
}

REST_AUTH_REGISTER_SERIALIZERS = {"REGISTER_SERIALIZER": "core.auth.serializers.CustomRegisterSerializer"}

# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 4
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_AUTHENTICATION_METHOD = "username_email"

ACCOUNT_CONFIRM_EMAIL_ON_GET = False
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
ACCOUNT_PRESERVE_USERNAME_CASING = False  # Always save username in lowercase

ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = False

ACCOUNT_ADAPTER = "core.auth.adapters.CustomAccountAdapter"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

# djangorestframework-simplejwt
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_KEY", default="69hW18tjBCjXwUfycIONtVXSnyrTIs949YthW18tjBCjXwUfycItgY0F"),
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

# PASSWORDS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    # {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Swagger Settings
# ------------------------------------------------------------------------------
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "JWT": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "USE_SESSION_AUTH": False,
}

# grappelli
# ------------------------------------------------------------------------------
GRAPPELLI_ADMIN_TITLE = "Peam Admin"

# STATIC
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR / "staticfiles")
STATIC_URL = "/static/"
# STATICFILES_DIRS = [str(APPS_DIR / "static")]
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
MEDIA_ROOT = str(ROOT_DIR / "media")
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "OPTIONS": {
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"


# FIXTURES
# ------------------------------------------------------------------------------
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False
# https://docs.djangoproject.com/en/3.0/ref/settings/#csrf-use-sessions
CSRF_USE_SESSIONS = False
# https://docs.djangoproject.com/en/3.0/ref/settings/#csrf-header-name
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
ADMIN_URL = "admin/"
ADMINS = [("""Abdelrahman Kandil""", "abdelrahmankandil@hotmail.com")]
MANAGERS = ADMINS

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}
