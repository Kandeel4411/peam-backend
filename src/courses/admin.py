from django.contrib import admin

from .models import Course, ProjectRequirement, Team, CourseInvitation
from .inlines import (
    CourseAttachmentInline,
    CourseTeacherInline,
    ProjectRequirementAttachmentInline,
    CourseStudentInline,
    TeamStudentInline,
)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [TeamStudentInline]


@admin.register(CourseInvitation)
class CourseInvitationAdmin(admin.ModelAdmin):
    pass


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseAttachmentInline, CourseTeacherInline, CourseStudentInline]


@admin.register(ProjectRequirement)
class ProjectRequirementAdmin(admin.ModelAdmin):
    inlines = [ProjectRequirementAttachmentInline]
