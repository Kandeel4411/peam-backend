from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core.utils.inlines import EmailAddressInline

User = get_user_model()


# TODO make username readonly and change forms accordingly
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [EmailAddressInline]
    fieldsets = (
        # original form fieldsets, expanded
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("email", "name", "avatar")}),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        # UserAdmin specific fieldsets used in creation
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    list_display = ("username", "email", "name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "name", "email")
    ordering = ("username",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    def has_delete_permission(self, request, obj=None):
        return False
