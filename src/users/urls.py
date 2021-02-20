from django.urls import path, include

from .views import UserView, UserDetailView

# User patterns
user_pattern = "users/"
user_detail_pattern = f"{user_pattern}<str:username>/"

urlpatterns = [
    path(user_pattern, UserView.as_view(), name="users"),
    path(user_detail_pattern, UserDetailView.as_view(), name="users-detail"),
]
