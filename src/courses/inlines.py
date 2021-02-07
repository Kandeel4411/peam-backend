from django.contrib import admin

from .models import CourseAttachment, CourseTeacher, ProjectRequirementAttachment, CourseStudent, TeamStudent


class ProjectRequirementAttachmentInline(admin.TabularInline):
    """
    A class for inlining project requirement attachments
    """

    model = ProjectRequirementAttachment


class CourseAttachmentInline(admin.TabularInline):
    """
    A class for inlining course attachments
    """

    model = CourseAttachment


class CourseTeacherInline(admin.TabularInline):
    """
    A class for inlining course teachers
    """

    model = CourseTeacher


class CourseStudentInline(admin.TabularInline):
    """
    A class for inlining course students
    """

    model = CourseStudent


class TeamStudentInline(admin.TabularInline):
    """
    A class for inlining team students
    """

    model = TeamStudent
