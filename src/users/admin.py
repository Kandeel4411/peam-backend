from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        *BaseUserAdmin.fieldsets,  # original form fieldsets, expanded
        (  # new fieldset added on to the bottom
            "Profile",  # group heading of your choice; set to None for a blank space instead of a header
            {
                "fields": ("avatar",),
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        return False
