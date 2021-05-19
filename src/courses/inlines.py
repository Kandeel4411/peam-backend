from django.contrib import admin

from .models import (
    CourseAttachment,
    CourseTeacher,
    ProjectRequirementAttachment,
    CourseStudent,
    TeamStudent,
    Project,
    ProjectRequirementGrade,
)


class ProjectRequirementAttachmentInline(admin.TabularInline):
    """
    A class for inlining project requirement attachments
    """

    model = ProjectRequirementAttachment
    extra = 0


class CourseAttachmentInline(admin.TabularInline):
    """
    A class for inlining course attachments
    """

    model = CourseAttachment
    extra = 0


class CourseTeacherInline(admin.TabularInline):
    """
    A class for inlining course teachers
    """

    model = CourseTeacher
    extra = 0


class CourseStudentInline(admin.TabularInline):
    """
    A class for inlining course students
    """

    model = CourseStudent
    extra = 0


class TeamStudentInline(admin.TabularInline):
    """
    A class for inlining team students
    """

    model = TeamStudent
    extra = 0


class ProjectInline(admin.TabularInline):
    """
    A class for inlining projects
    """

    model = Project
    extra = 0


class ProjectRequirementGradeInline(admin.TabularInline):
    """
    A class for inlining project requirement grades
    """

    model = ProjectRequirementGrade
    extra = 0
