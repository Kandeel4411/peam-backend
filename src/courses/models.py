import uuid
import zipfile
from typing import Optional

from django.db import models, transaction
from django.db import IntegrityError
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import CICharField
from django.core.exceptions import ValidationError
from allauth.account.adapter import get_adapter
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from core.utils.tz import local_timezone_now
from core.models import BaseInvitation
from core.constants import InvitationStatus
from .constants import CourseInvitationType


class Course(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE, related_name="courses_owned"
    )
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    code = CICharField(max_length=10, blank=False, null=False, verbose_name=_("Code"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    teachers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_taught", through="CourseTeacher")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_taken", through="CourseStudent")

    class Meta:
        managed = True
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        constraints = [models.UniqueConstraint(fields=["owner", "code"], name="unique_course")]
        indexes = [models.Index(fields=("owner",), name="%(class)s_owner_index")]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = _("Course Teacher")
        verbose_name_plural = _("Course Teachers")
        constraints = [models.UniqueConstraint(fields=["course", "teacher"], name="unique_course_Teacher")]

    def __str__(self) -> str:
        return f"{self.teacher} - {self.course}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Enforcing that if already in the course as a student then return an error
        if CourseStudent._default_manager.filter(student_id=self.teacher_id, course_id=self.course_id).exists():
            raise ValidationError(
                {"course": _("Can't be both a teacher and a student to the same course.")},
            )


class CourseStudent(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = _("Course Student")
        verbose_name_plural = _("Course Students")
        constraints = [models.UniqueConstraint(fields=["student", "course"], name="unique_course_student")]

    def __str__(self) -> str:
        return f"{self.student} - {self.course}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Enforcing that if already in the course as a teacher then return an error
        if CourseTeacher._default_manager.filter(teacher_id=self.student_id, course_id=self.course_id).exists():
            raise ValidationError(
                {"course": _("Can't be both a student and a teacher to the same course.")},
            )


class ProjectRequirement(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="requirements")
    title = CICharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    to_dt = models.DateTimeField(blank=False, verbose_name=_("Deadline"))
    from_dt = models.DateTimeField(default=timezone.now, blank=True, verbose_name=("Start date"))
    total_marks = models.DecimalField(
        verbose_name=_("Total Marks"),
        blank=True,
        null=True,
        decimal_places=2,
        max_digits=4,
        validators=[MinValueValidator(limit_value=0, message="Total marks can't be zero or below.")],
    )

    class Meta:
        managed = True
        verbose_name = _("Project Requirement")
        verbose_name_plural = _("Project Requirements")
        constraints = [
            models.CheckConstraint(check=models.Q(from_dt__lte=models.F("to_dt")), name="date_constraint"),
            models.UniqueConstraint(fields=["title", "course"], name="unique_project_requirement"),
        ]

    def __str__(self) -> str:
        from_dt = f"{timezone.localtime(self.from_dt):%Y-%m-%d}"
        to_dt = f"{timezone.localtime(self.to_dt):%Y-%m-%d}"
        return f"{self.course} from {from_dt} to {to_dt}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Case: Checking that from_dt isn't larger than to_dt
        if (self.to_dt and self.from_dt) and self.from_dt > self.to_dt:
            raise ValidationError(
                {"to_dt": _("Start date can't be less than the deadline.")},
            )


class ProjectRequirementGrade(models.Model):
    requirement = models.ForeignKey(ProjectRequirement, to_field="uid", on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE, related_name="grades"
    )
    marks = models.DecimalField(
        verbose_name=_("Marks"),
        blank=False,
        null=False,
        decimal_places=2,
        max_digits=4,
        validators=[MinValueValidator(limit_value=-1, message="Marks can't be below zero.")],
    )
    note = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Note"))

    class Meta:
        managed = True
        verbose_name = "Project Requirement Grade"
        verbose_name_plural = "Project Requirement Grades"
        constraints = [
            models.UniqueConstraint(fields=["student", "requirement"], name="unique_requirement_grade"),
        ]
        indexes = [models.Index(fields=("requirement",), name="%(class)s_index")]

    def __str__(self) -> str:
        return f"{self.requirement}: {self.student} got {self.mark}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Checking if the mark isn't higher than the set requirement total mark
        if (total_marks := self.requirement.total_marks) is not None:
            if self.marks > total_marks:
                raise ValidationError(
                    {"marks": _("Marks given can't be higher than the set total marks.")},
                )


class ProjectRequirementAttachment(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(
        ProjectRequirement, to_field="uid", on_delete=models.CASCADE, related_name="attachments"
    )
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    link = models.URLField(blank=False, null=False, verbose_name=_("Link"))

    class Meta:
        managed = True
        verbose_name = "Project Requirement Attachment"
        verbose_name_plural = "Project Requirement Attachments"

    def __str__(self) -> str:
        from_dt = f"{timezone.localtime(self.requirement.from_dt):%Y-%m-%d}"
        to_dt = f"{timezone.localtime(self.requirement.to_dt):%Y-%m-%d}"
        return f"{self.requirement.title} [{from_dt} - {to_dt}]: {self.title}"


class CourseAttachment(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    link = models.URLField(blank=False, null=False, verbose_name=_("Link"))

    class Meta:
        managed = True
        verbose_name = "Course Attachment"
        verbose_name_plural = "Course Attachments"

    def __str__(self) -> str:
        return f"{self.course.code}: {self.title}"


class Team(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = CICharField(max_length=50, blank=False, null=False, verbose_name=_("Name"))
    requirement = models.ForeignKey(ProjectRequirement, to_field="uid", on_delete=models.CASCADE, related_name="teams")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="teams", through="TeamStudent")

    class Meta:
        managed = True
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        constraints = [models.UniqueConstraint(fields=["name", "requirement"], name="unique_team")]
        indexes = [models.Index(fields=("requirement",), name="%(class)s_requirement_index")]

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


def _project_upload_path(instance: "Project", filename: str) -> str:
    """
    Custom Callable that is passed to django's FileField for uploading

    Uploads files under "projects/req_<requirement-uid>/<team-name>_<filename>"

    """
    return f"projects/req_{instance.team.requirement_id}/{instance.team.name}_{filename}"


class Project(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    team = models.OneToOneField(Team, on_delete=models.CASCADE, to_field="uid")
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    project_zip = models.FileField(
        verbose_name=_("Project Compressed file"), upload_to=_project_upload_path, blank=False, null=False
    )

    class Meta:
        managed = True
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self) -> str:
        return f"{self.team} - {self.title}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        if self.project_zip._file is not None:
            if not zipfile.is_zipfile(self.project_zip.file):
                raise ValidationError({"project_zip": _('Can only upload ".zip" compressed files')})
            try:
                # Checking integrity of zipfile
                with zipfile.ZipFile(self.project_zip.file) as zfile:
                    if zfile.testzip() is not None:
                        raise ValidationError(
                            {
                                "project_zip": _(
                                    "Faulty files were found in the zip file. Please upload a valid zip file"
                                )
                            }
                        )
            except zipfile.BadZipfile:
                raise ValidationError(
                    {"project_zip": _("Wasn't able to open zip file. Please upload a valid zip file.")}
                )


class TeamStudent(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Team Student"
        verbose_name_plural = "Team Students"
        constraints = [models.UniqueConstraint(fields=["student", "team"], name="unique_team_student")]

    def __str__(self) -> str:
        return f"{self.student} - {self.team}"

    def validate_unique(self, *args, **kwargs) -> None:
        """
        Custom validate unique method
        """
        super().validate_unique(*args, **kwargs)

        # Enforcing that student can only belong to one team in each project requirement
        if self.__class__._default_manager.filter(
            ~models.Q(pk=self.pk), student_id=self.student_id, team__requirement_id=self.team.requirement_id
        ).exists():
            raise ValidationError(
                {"student": _("Student already belongs to another team.")},
            )

    def delete(self, *args, **kwargs):
        """
        Custom deletion call
        """
        student_count = self.__class__._default_manager.filter(team_id=self.team_id).count()
        return_data = super().delete(*args, **kwargs)

        # This is the last team student, therefore delete team
        if student_count == 1:
            self.team.delete()
        return return_data


class CourseInvitation(BaseInvitation):
    email = models.EmailField(blank=False, null=False, verbose_name=_("Email address"))
    type = models.CharField(choices=CourseInvitationType.INVITE_CHOICES, max_length=30, blank=False, null=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="invitations")

    class Meta(BaseInvitation.Meta):
        abstract = False
        managed = True
        verbose_name = "Course Invitation"
        verbose_name_plural = "Course Invitations"
        constraints = BaseInvitation.Meta.constraints + [
            models.CheckConstraint(
                check=models.Q(type__in=CourseInvitationType.INVITE_LIST),
                name="%(class)s_type_constraint",
            )
        ]

    def __str__(self) -> str:
        return f"{self.sender} invited {self.email}[{self.type}] to {self.course}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Calling BaseInvitation clean hook
        super().clean()

        # Enforcing that if already in the course as either a student or a teacher then return an error
        if CourseStudent._default_manager.filter(student__email=self.email, course_id=self.course_id).exists():
            raise ValidationError(
                {"email": _("A course student with this email already exists.")},
            )
        elif CourseTeacher._default_manager.filter(teacher__email=self.email, course_id=self.course_id).exists():
            raise ValidationError(
                {"email": _("A course teacher with this email already exists.")},
            )

        # Sender can't invite himself
        if self.sender.email == self.email:
            raise ValidationError({"sender": _("Sender can't invite himself to the course")})

        # If the invite is for a teacher then only the course owner can invite them
        if self.course.owner != self.sender and self.type == CourseInvitationType.TEACHER_INVITE:
            raise ValidationError({"type": _("Only the course owner can invite other teachers.")})

        # only course teachers can invite
        if not CourseTeacher._default_manager.filter(teacher_id=self.sender_id, course_id=self.course_id).exists():
            raise ValidationError({"sender": _("Only course teachers can send a course invite")})

    def validate_unique(self, *args, **kwargs) -> None:
        """
        Custom validate unique method
        """
        super().validate_unique(*args, **kwargs)

        # Enforcing the uniqueness of email to course if an existing invite didn't expire or was rejected and accepted
        # Note: The reason why we aren't checking on accepted is because of this scenario: a user changed his email and
        # created another account with the old email which would render the previously accepted invitation invalid for
        # the old email.
        if CourseInvitation._default_manager.filter(
            ~models.Q(pk=self.pk), email=self.email, course_id=self.course_id, status=InvitationStatus.PENDING
        ).exists():
            raise ValidationError({"email": _("A course invitation with this email already exists that is pending.")})

    @classmethod
    def send_invitation(
        cls, request, email_template_prefix="invitations/course/email_invite", *args, **kwargs
    ) -> "CourseInvitation":
        """
        Helper method that wraps creation of a course invitation and sends an email and
        returns created course invitation instance if successful.

        :request: django http request

        :email_template: template that is going to be used for
        the invitation(site_name, email, invite_url, expiry_date, sender and course are available in ctx)

        :*args, **kwargs: arguments that are going to be directly passed to default manager object creation
        method.

        *Note:* This method should generally be used instead of manual creation of course invitation as
        it ensures that if creation fails, an email wont be sent and vice versa
        """

        adapter = get_adapter(request)
        site = get_current_site(request)
        protocol: str = settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL
        invite_url: str = f"{protocol}://{site.domain}{reverse('login')}"

        with transaction.atomic():
            invitation: cls = cls._default_manager.create(*args, **kwargs)

            # Adding Invitation token as a query param to the invite url
            invite_url += f"{settings.FRONTEND_COURSE_INVITATION_PARAM}={invitation.token}"

            # Show sender name if its present
            sender = invitation.sender
            if not sender.name:
                sender = sender.username
            else:
                sender = sender.name.title()

            email_template_ctx = {
                "invite_url": invite_url,
                "email": invitation.email,
                "site_name": site.domain,
                "course": invitation.course.title,
                "sender": sender,
                "expiry_date": f"{timezone.localtime(invitation.expiry_date):%Y-%m-%d}",
            }
            adapter.send_mail(email_template_prefix, invitation.email, email_template_ctx)

            return invitation


class TeamInvitation(BaseInvitation):
    email = models.EmailField(blank=False, null=False, verbose_name=_("Email address"))
    team = models.ForeignKey(Team, to_field="uid", on_delete=models.CASCADE, related_name="invitations")

    class Meta(BaseInvitation.Meta):
        abstract = False
        managed = True
        verbose_name = "Team Invitation"
        verbose_name_plural = "Team Invitations"
        constraints = BaseInvitation.Meta.constraints

    def __str__(self) -> str:
        return f"{self.sender} invited {self.email} to {self.team}"

    def clean(self) -> None:
        """
        Model level validation hook
        """
        # Calling BaseInvitation clean hook
        super().clean()

        # Enforcing that a student can only belong to one team in each project requirement
        if TeamStudent._default_manager.filter(
            student__email=self.email, team__requirement_id=self.team.requirement_id
        ).exists():
            raise ValidationError(
                {"email": _("A team student with this email already exists.")},
            )

        # Cant invite a none course student
        if not CourseStudent._default_manager.filter(
            student__email=self.email, course_id=self.team.requirement.course_id
        ).exists():
            raise ValidationError({"email": _("Can only invite students that are in the course.")})

        # Sender can't invite himself
        if self.sender.email == self.email:
            raise ValidationError({"sender": _("Sender can't invite himself to the team")})

        # Only existing team members can invite
        if not TeamStudent._default_manager.filter(student_id=self.sender_id, team_id=self.team_id).exists():
            raise ValidationError({"sender": _("Only team members can send a team invite")})

    def validate_unique(self, *args, **kwargs) -> None:
        """
        Custom validate unique method
        """
        super().validate_unique(*args, **kwargs)

        # Enforcing the uniqueness of email to course if an existing invite didn't expire or was rejected and accepted
        # Note: The reason why we aren't checking on accepted is because of this scenario: a user changed his email and
        # created another account with the old email which would render the previously accepted invitation invalid for
        # the old email.
        if TeamInvitation._default_manager.filter(
            ~models.Q(pk=self.pk), email=self.email, team_id=self.team_id, status=InvitationStatus.PENDING
        ).exists():
            raise ValidationError({"email": _("A team invitation with this email already exists that is pending.")})

    @classmethod
    def send_invitation(
        cls, request, email_template_prefix="invitations/team/email_invite", *args, **kwargs
    ) -> "CourseInvitation":
        """
        Helper method that wraps creation of a team invitation and sends an email and
        returns created team invitation instance if successful.

        :request: django http request

        :email_template: template that is going to be used for
        the invitation(site_name, email, invite_url, expiry_date, sender and team are available in ctx)

        :*args, **kwargs: arguments that are going to be directly passed to default manager object creation
        method.

        *Note:* This method should generally be used instead of manual creation of team invitation as
        it ensures that if creation fails, an email wont be sent and vice versa
        """

        adapter = get_adapter(request)
        site = get_current_site(request)
        protocol: str = settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL
        invite_url: str = f"{protocol}://{site.domain}{reverse('login')}"

        with transaction.atomic():
            invitation: cls = cls._default_manager.create(*args, **kwargs)

            # Adding Invitation token as a query param to the invite url
            invite_url += f"{settings.FRONTEND_TEAM_INVITATION_PARAM}={invitation.token}"

            # Show sender name if its present
            sender = invitation.sender
            if not sender.name:
                sender = sender.username
            else:
                sender = sender.name.title()

            email_template_ctx = {
                "invite_url": invite_url,
                "team": invitation.team.name,
                "site_name": site.domain,
                "email": invitation.email,
                "sender": sender,
                "expiry_date": f"{timezone.localtime(invitation.expiry_date):%Y-%m-%d}",
            }
            adapter.send_mail(email_template_prefix, invitation.email, email_template_ctx)

            return invitation
