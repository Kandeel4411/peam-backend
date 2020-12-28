from django.contrib import admin

from .models import CourseAttachment, CourseTeacher


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
