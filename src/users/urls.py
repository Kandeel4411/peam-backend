from django.urls import path, include

from .views import UserView

# User patterns
user_pattern = "users/"

urlpatterns = [
    path(user_pattern, UserView.as_view(), name="users"),
]
