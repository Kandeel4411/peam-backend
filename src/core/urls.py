from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from dj_rest_auth.views import PasswordResetConfirmView
from dj_rest_auth.registration.views import VerifyEmailView, ConfirmEmailView


schema_view = get_schema_view(
    openapi.Info(
        title="Peam API",
        default_version="v1",
        description="Automatically generated API docs",
        contact=openapi.Contact(email="abdelrahmankandil@hotmail.com"),
    ),
)

api_patterns = [
    path("api/v1/", include("courses.urls")),
    path(
        "api/v1/auth/password/reset/confirm/<slug:uidb64>/<slug:token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("api/v1/auth/", include("dj_rest_auth.urls"), name="rest_auth"),
    path(
        "api/v1/signup/account-confirm-email/<str:key>/",
        ConfirmEmailView.as_view(),
        name="account_email_verification_done",
    ),
    path("api/v1/signup/", include("dj_rest_auth.registration.urls"), name="rest_signup"),
    path("api/v1/signup/account-confirm-email/", VerifyEmailView.as_view(), name="account_email_verification_sent"),
]

urlpatterns = (
    [
        # Api Doc homepage
        path("", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
        path("", include(api_patterns)),
        path("grappelli/", include("grappelli.urls")),  # grappelli URLS
        path(settings.ADMIN_URL, admin.site.urls),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # noqa: W503
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # noqa: W503
)
