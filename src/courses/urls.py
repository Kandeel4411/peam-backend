from django.urls import path, include

from .views import (
    CourseView,
    CourseDetailView,
    ProjectRequirementDetailView,
    CourseAttachmentDetailView,
    ProjectRequirementAttachmentDetailView,
)


# Course patterns
course_pattern = "courses/"
course_detail_pattern = f"{course_pattern}<str:owner>/<str:code>/"

# Project requirement patterns
requirement_pattern = f"{course_detail_pattern}requirements/"
requirement_detail_pattern = f"{requirement_pattern}<str:title>/"

# Project requirement attachment patterns
requirement_attachment_pattern = f"{requirement_detail_pattern}attachments/"
requirement_attachment_detail_pattern = f"{requirement_attachment_pattern}<str:uid>/"

# Course attachment patterns
course_attachment_pattern = f"{course_detail_pattern}attachments/"
course_attachment_detail_pattern = f"{course_attachment_pattern}<str:uid>/"

urlpatterns = [
    path(course_pattern, CourseView.as_view(), name="courses"),
    path(course_detail_pattern, CourseDetailView.as_view(), name="course-detail"),
    path(course_attachment_detail_pattern, CourseAttachmentDetailView.as_view(), name="course-attachment-detail"),
    path(requirement_detail_pattern, ProjectRequirementDetailView.as_view(), name="project-requirement-detail"),
    path(
        requirement_attachment_detail_pattern,
        ProjectRequirementAttachmentDetailView.as_view(),
        name="project-requirement-attachment-detail",
    ),
]
