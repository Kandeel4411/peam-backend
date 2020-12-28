from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Peam API",
        default_version="v1",
        description="Automatically generated API docs",
        contact=openapi.Contact(email="abdelrahmankandil@hotmail.com"),
    ),
)

api_patterns = [path("api/docs", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc")]

urlpatterns = (
    [
        path("", include(api_patterns)),
        path("grappelli/", include("grappelli.urls")),  # grappelli URLS
        path(settings.ADMIN_URL, admin.site.urls),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # noqa: W503
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # noqa: W503
)
