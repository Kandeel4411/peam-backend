from django.urls import path, include

from .invites.views import (
    CourseInvitationView,
    CourseInvitationDetailView,
    TeamInvitationView,
    TeamInvitationDetailView,
)
from .views import (
    CourseView,
    CourseStudentView,
    CourseTeacherView,
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
course_invitation_detail_pattern = f"{course_invitation_pattern}<str:token>/"

# Course student patterns
course_student_pattern = f"{course_detail_pattern}students/"

# Course teacher patterns
course_teacher_pattern = f"{course_detail_pattern}teachers/"

# Project requirement patterns
requirement_pattern = f"{course_detail_pattern}requirements/"
requirement_detail_pattern = f"{requirement_pattern}<str:requirement_title>/"

# Project requirement attachment patterns
requirement_attachment_pattern = f"{requirement_detail_pattern}attachments/"
requirement_attachment_detail_pattern = f"{requirement_attachment_pattern}<slug:attachment_uid>/"

# Project requirement team patterns
requirement_team_pattern = f"{requirement_detail_pattern}teams/"
requirement_team_detail_pattern = f"{requirement_team_pattern}<str:team_name>/"

# Project requirement team invitation patterns
requirement_team_invitation_pattern = f"{requirement_team_detail_pattern}invitations/"
requirement_team_invitation_detail_pattern = f"{requirement_team_invitation_pattern}<str:invitation_token>/"

# Course attachment patterns
course_attachment_pattern = f"{course_detail_pattern}attachments/"
course_attachment_detail_pattern = f"{course_attachment_pattern}<slug:attachment_uid>/"

urlpatterns = [
    path(course_pattern, CourseView.as_view(), name="courses"),
    path(course_detail_pattern, CourseDetailView.as_view(), name="courses-detail"),
    path(course_student_pattern, CourseStudentView.as_view(), name="students"),
    path(course_teacher_pattern, CourseTeacherView.as_view(), name="teachers"),
    path(course_invitation_pattern, CourseInvitationView.as_view(), name="course-invitations"),
    path(course_invitation_detail_pattern, CourseInvitationDetailView.as_view(), name="course-invitations-detail"),
    path(course_attachment_pattern, CourseAttachmentView.as_view(), name="course-attachments"),
    path(course_attachment_detail_pattern, CourseAttachmentDetailView.as_view(), name="course-attachments-detail"),
    path(requirement_pattern, ProjectRequirementView.as_view(), name="requirements"),
    path(requirement_detail_pattern, ProjectRequirementDetailView.as_view(), name="requirements-detail"),
    path(
        requirement_team_pattern,
        TeamView.as_view(),
        name="teams",
    ),
    path(
        requirement_team_detail_pattern,
        TeamDetailView.as_view(),
        name="teams-detail",
    ),
    path(
        requirement_attachment_pattern,
        ProjectRequirementAttachmentView.as_view(),
        name="requirement-attachments",
    ),
    path(
        requirement_attachment_detail_pattern,
        ProjectRequirementAttachmentDetailView.as_view(),
        name="requirement-attachments-detail",
    ),
    path(
        requirement_team_invitation_pattern,
        TeamInvitationView.as_view(),
        name="team-invitations",
    ),
    path(
        requirement_team_invitation_detail_pattern,
        TeamInvitationDetailView.as_view(),
        name="team-invitations-detail",
    ),
]
