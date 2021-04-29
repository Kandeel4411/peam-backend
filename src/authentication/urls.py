from django.conf import settings
from django.urls import path

from dj_rest_auth.registration.views import RegisterView, VerifyEmailView
from dj_rest_auth.views import (
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
)

from .views import LoginView  # Already .as_view


# Authentication / Registration routes
urlpatterns = [
    path("auth/signup/", RegisterView.as_view(), name="rest_register"),
    # Route to confirm email
    path("auth/signup/verify-email/", VerifyEmailView.as_view(), name="account_email_verification_sent"),
    # Route to email form to reset password
    path("auth/password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    # Route to reset password
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="rest_password_reset_confirm",
    ),
    path("auth/login/", LoginView, name="rest_login"),
    # Routes that require logged in user
    path("auth/logout/", LogoutView.as_view(), name="rest_logout"),
]


if getattr(settings, "REST_USE_JWT", False):
    from rest_framework_simplejwt.views import TokenVerifyView
    from dj_rest_auth.jwt_auth import get_refresh_view

    urlpatterns += [
        path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
        path("auth/token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    ]
