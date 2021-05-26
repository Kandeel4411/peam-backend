from django.urls import path, include

from .views import ResourcesLocatorView

# Resources locator patterns
resources_locator_pattern = "locator/"

urlpatterns = [
    path(resources_locator_pattern, ResourcesLocatorView.as_view(), name="locator"),
]
