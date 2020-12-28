from django.contrib import admin

from .models import Team
from .inlines import TeamMemberInline


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [TeamMemberInline]
