from django.contrib import admin

from .models import Course, ProjectRequirement
from .inlines import CourseAttachmentInline, CourseTeacherInline, ProjectRequirementAttachmentInline


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseAttachmentInline, CourseTeacherInline]


@admin.register(ProjectRequirement)
class ProjectRequirementAdmin(admin.ModelAdmin):
    inlines = [ProjectRequirementAttachmentInline]
