from django.urls import path, include

from .views import (
    UserView,
    UserDetailView,
    BaseUserAvatarView,
    BaseUserPasswordChangeView,
    BaseUserView,
    BaseUserProfileView,
)

# User patterns
user_pattern = "users/"
user_detail_pattern = f"{user_pattern}<str:username>/"

# Base User patterns
base_user_pattern = "user/"
avatar_base_user_pattern = f"{base_user_pattern}avatar/"
profile_base_user_pattern = f"{base_user_pattern}profile/"
password_base_user_pattern = f"{base_user_pattern}password/change/"

urlpatterns = [
    path(user_pattern, UserView.as_view(), name="users"),
    path(user_detail_pattern, UserDetailView.as_view(), name="users-detail"),
    path(base_user_pattern, BaseUserView.as_view(), name="user"),
    path(avatar_base_user_pattern, BaseUserAvatarView.as_view(), name="user-avatar"),
    path(profile_base_user_pattern, BaseUserProfileView.as_view(), name="user-profile"),
    path(password_base_user_pattern, BaseUserPasswordChangeView, name="user-password-change"),
]
