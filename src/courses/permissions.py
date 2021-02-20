from rest_framework import permissions
from django.utils.translation import gettext_lazy as _

from .models import (
    Course,
    CourseStudent,
    CourseTeacher,
    Team,
    ProjectRequirement,
    CourseAttachment,
    ProjectRequirementAttachment,
)
from .utils import is_course_student, is_course_teacher, is_course_owner, is_team_student


class CourseDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: Course) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.uid) or is_course_student(
                user=request.user, course_id=obj.uid
            )

        # Only course teachers can update
        elif request.method == "PATCH":
            self.message = _("Only course teachers can update.")
            teacher_check = is_course_teacher(user=request.user, course_id=obj.uid)
            if not teacher_check:
                return False
            # Only course owner can transfer ownership
            elif "owner" in request.data:
                self.message = _("Only the course owner can transfer ownership.")
                return is_course_owner(user=request.user, course_id=obj.uid)

        # Only the course owner can delete
        elif request.method == "DELETE":
            self.message = _("Only the course owner can delete.")
            return is_course_owner(user=request.user, course_id=obj.uid)

        return True


class CourseStudentViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseStudentView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        return True


class CourseStudentDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseStudentDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: CourseStudent) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only course teachers can delete
        elif request.method == "DELETE":
            self.message = _("Only the course teachers can remove a student.")
            return is_course_teacher(user=request.user, course_id=obj.course_id)

        return True


class CourseTeacherViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseTeacherView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        return True


class CourseTeacherDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseTeacherDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: CourseTeacher) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only the course owner can delete
        elif request.method == "DELETE":
            self.message = _("Only the course owner can remove a teacher.")
            return is_course_owner(user=request.user, course_id=obj.course_id)

        return True


class ProjectRequirementViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the ProjectRequirementView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        # Only course teachers can create a project requirement
        elif request.method == "POST":
            self.message = _("Only course teachers can create a project requirement.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username)

        return True


class ProjectRequirementDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the ProjectRequirementDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: ProjectRequirement) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only course teachers can update or delete a requirement
        elif request.method in ["PATCH", "DELETE"]:
            self.message = _("Only course teachers can a update or delete project requirement.")
            return is_course_teacher(user=request.user, course_id=obj.course_id)

        return True


class TeamViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the TeamView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        # Only course students can create a team
        elif request.method == "POST":
            self.message = _("Only course students can create a team.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_student(user=request.user, code=code, owner_username=username)

        return True


class TeamDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the TeamDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: Team) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.requirement.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only course teachers and team members can update or delete a team
        elif request.method in ["PATCH", "DELETE"]:
            self.message = _("Only course teachers and team members can update or delete a team.")
            return is_course_teacher(user=request.user, course_id=obj.requirement.course_id) or is_team_student(
                user=request.user, team_id=obj.uid
            )

        return True


class CourseAttachmentViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseAttachmentView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        # Only course teachers can create a course attachment
        elif request.method == "POST":
            self.message = _("Only course teachers can create a course attachment.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username)

        return True


class CourseAttachmentDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the CourseAttachmentDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: CourseAttachment) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only course teachers can update or delete a course attachment
        elif request.method in ["PATCH", "DELETE"]:
            self.message = _("Only course teachers can a update or delete course attachment.")
            return is_course_teacher(user=request.user, course_id=obj.course_id)

        return True


class ProjectRequirementAttachmentViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the ProjectRequirementAttachmentView
    """

    message = None

    def has_permission(self, request, view):
        """
        Checks general view permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username) or is_course_student(
                user=request.user, code=code, owner_username=username
            )

        # Only course teachers can create a course attachment
        elif request.method == "POST":
            self.message = _("Only course teachers can create a course attachment.")
            code: str = view.kwargs["course_code"]
            username: str = view.kwargs["course_owner"]

            return is_course_teacher(user=request.user, code=code, owner_username=username)

        return True


class ProjectRequirementAttachmentDetailViewPermission(permissions.BasePermission):
    """
    Base permission that applies checks for the ProjectRequirementAttachmentDetailView
    """

    message = None

    def has_object_permission(self, request, view, obj: ProjectRequirementAttachment) -> bool:
        """
        Checks object level permissions
        """

        # Only those who belong to the course can retrieve
        if request.method == "GET":
            self.message = _("User must be either a student or a teacher of the course.")
            return is_course_teacher(user=request.user, course_id=obj.course_id) or is_course_student(
                user=request.user, course_id=obj.course_id
            )

        # Only course teachers can update or delete a project requirement attachment
        elif request.method in ["PATCH", "DELETE"]:
            self.message = _("Only course teachers can a update or delete project requirement attachment.")
            return is_course_teacher(user=request.user, course_id=obj.course_id)

        return True
