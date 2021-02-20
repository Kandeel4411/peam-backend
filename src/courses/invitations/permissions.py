from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

from courses.utils import is_course_student, is_course_teacher, is_course_owner, is_team_student
from courses.models import CourseInvitation, TeamInvitation


class CourseInvitationViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseInvitationView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only course teachers can view the course invitations
        if request.method == "GET":
            self.message = _("Only teachers can view the course invitations.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username)

        # Only course teachers can send a course invitation
        elif request.method == "POST":
            self.message = _("Only course teachers can send a course invitation.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]
            return is_course_teacher(user=request.user, code=code, owner_username=username)

        return True


class CourseInvitationDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseInvitationDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: CourseInvitation) -> bool:
        """
        Checks object level permissions
        """

        # Only course teachers can can view a course invitation
        if request.method == "GET":
            self.message = _("Only course teachers can view a course invitation.")
            return is_course_teacher(user=request.user, course_id=obj.course_id)

        # Only the course owner can delete a course invitation
        elif request.method == "DELETE":
            self.message = _("Only the course owner can delete a course invitation.")
            return is_course_owner(user=request.user, course_id=obj.course_id)

        # Only the user the invitation belongs to can accept or decline.
        elif request.method == "POST":
            self.message = _("Only the user the invitation belongs to can accept or decline.")
            return request.user.email == obj.email

        return True


class TeamInvitationViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the TeamInvitationView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only team members can view the team invitations
        if request.method == "GET":
            self.message = _("Only team members can view the team invitations")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]
            title = view.kwargs["requirement_title"]

            return is_team_student(user=request.user, owner_username=username, code=code, requirement_title=title)

        # Only team members can send a team invitation
        elif request.method == "POST":
            self.message = _("Only team members can send a team invitation.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]
            title = view.kwargs["requirement_title"]

            return is_team_student(user=request.user, owner_username=username, code=code, requirement_title=title)

        return True


class TeamInvitationDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the TeamInvitationDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: TeamInvitation) -> bool:
        """
        Checks object level permissions
        """

        # Only team members can view a team invitation
        if request.method == "GET":
            self.message = _("Only team members can view a team invitation.")
            return is_team_student(user=request.user, team_id=obj.team_id)

        # Only team members can delete a team invitation
        elif request.method == "DELETE":
            self.message = _("Only team members can delete a team invitation.")
            return is_course_owner(user=request.user, team_id=obj.team_id)

        # Only the user the invitation belongs to can accept or decline.
        elif request.method == "POST":
            self.message = _("Only the user the invitation belongs to can accept or decline.")
            return request.user.email == obj.email

        return True
