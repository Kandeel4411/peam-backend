from django.urls import path, include

from .invites.views import CourseInvitationView, CourseInvitationDetailView
from .views import (
    CourseView,
    CourseDetailView,
    TeamView,
    TeamDetailView,
    ProjectRequirementView,
    ProjectRequirementDetailView,
    CourseAttachmentView,
    CourseAttachmentDetailView,
    ProjectRequirementAttachmentView,
    ProjectRequirementAttachmentDetailView,
)


# Course patterns
course_pattern = "courses/"
course_detail_pattern = f"{course_pattern}<str:course_owner>/<str:course_code>/"

# Course invitation patterns
course_invitation_pattern = f"{course_detail_pattern}invitations/"
course_invitation_detail_pattern = f"{course_detail_pattern}invitations/<str:token>/"

# Project requirement patterns
requirement_pattern = f"{course_detail_pattern}requirements/"
requirement_detail_pattern = f"{requirement_pattern}<str:requirement_title>/"

# Project requirement attachment patterns
requirement_attachment_pattern = f"{requirement_detail_pattern}attachments/"
requirement_attachment_detail_pattern = f"{requirement_attachment_pattern}<slug:attachment_uid>/"

# Project requirement team patterns
requirement_team_pattern = f"{requirement_detail_pattern}teams/"
requirement_team_detail_pattern = f"{requirement_team_pattern}<str:team_name>/"

# Course attachment patterns
course_attachment_pattern = f"{course_detail_pattern}attachments/"
course_attachment_detail_pattern = f"{course_attachment_pattern}<slug:attachment_uid>/"

urlpatterns = [
    path(course_pattern, CourseView.as_view(), name="courses"),
    path(course_detail_pattern, CourseDetailView.as_view(), name="course-detail"),
    path(course_invitation_pattern, CourseInvitationView.as_view(), name="course-invitation"),
    path(course_invitation_detail_pattern, CourseInvitationDetailView.as_view(), name="course-invitation-detail"),
    path(course_attachment_pattern, CourseAttachmentView.as_view(), name="course-attachment"),
    path(course_attachment_detail_pattern, CourseAttachmentDetailView.as_view(), name="course-attachment-detail"),
    path(requirement_pattern, ProjectRequirementView.as_view(), name="project-requirement"),
    path(requirement_detail_pattern, ProjectRequirementDetailView.as_view(), name="project-requirement-detail"),
    path(
        requirement_team_pattern,
        TeamView.as_view(),
        name="team",
    ),
    path(
        requirement_team_detail_pattern,
        TeamDetailView.as_view(),
        name="team-detail",
    ),
    path(
        requirement_attachment_pattern,
        ProjectRequirementAttachmentView.as_view(),
        name="project-requirement-attachment",
    ),
    path(
        requirement_attachment_detail_pattern,
        ProjectRequirementAttachmentDetailView.as_view(),
        name="project-requirement-attachment-detail",
    ),
]
