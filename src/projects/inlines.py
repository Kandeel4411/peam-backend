from django.contrib import admin

from .models import TeamMember


class TeamMemberInline(admin.TabularInline):
    """
    A class for inlining team members
    """

    model = TeamMember
