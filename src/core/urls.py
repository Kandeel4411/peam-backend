from django.contrib import admin
from django.conf import settings
from django.views.generic.base import TemplateView
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.permissions import AllowAny

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Api routes
api_patterns = [
    path("api/v1/", include("courses.urls")),
    path("api/v1/", include("users.urls")),
    path("api/v1/", include("authentication.urls"), name="rest_auth"),
]


schema_view = get_schema_view(
    openapi.Info(
        title="Peam API",
        default_version="v1",
        description="Automatically generated API docs",
        contact=openapi.Contact(email="abdelrahmankandil@hotmail.com"),
    ),
    patterns=api_patterns,
    permission_classes=(AllowAny,),  # TODO Close this in the future
    public=True,
)

# General routes
urlpatterns = (
    [
        # Api Doc homepage
        path("", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
        path("", include(api_patterns)),
        path(  # Required route with name "account_confirm_email" that is sent to user email on sign up
            settings.FRONTEND_EMAIL_CONFIRMATION_URL,
            TemplateView.as_view(),  # ? Just a stub view
            name="account_confirm_email",
        ),
        path(  # Required route with name "password_reset_confirm" that is sent to user email on reset
            settings.FRONTEND_PASSWORD_RESET_CONFIRMATION_URL,
            TemplateView.as_view(),  # ? Just a stub view
            name="password_reset_confirm",
        ),
        path(  # Required route with name "login" that is sent to user email
            settings.FRONTEND_LOGIN_URL,
            TemplateView.as_view(),  # ? Just a stub view
            name="login",
        ),
        path("grappelli/", include("grappelli.urls")),  # grappelli URLS
        path(settings.ADMIN_URL, admin.site.urls),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # noqa: W503
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # noqa: W503
)
