from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class UserDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the UserDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: User) -> bool:
        """
        Checks object level permissions
        """

        # Only the user can delete his own account
        if request.method == "DELETE":
            self.message = _("Only the user can delete his own account.")
            return request.user == obj

        # Only the user can update his profile.
        elif request.method == "POST":
            self.message = _("Only the user can update his profile.")
            return request.user == obj

        return True
