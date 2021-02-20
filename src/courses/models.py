import uuid
from typing import Optional

from django.db import models, transaction
from django.db import IntegrityError
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
from .constants import CourseInvitationType


class Course(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE, related_name="courses"
    )
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    code = CICharField(max_length=10, blank=False, null=False, verbose_name=_("Code"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    teachers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="as_teacher_set", through="CourseTeacher")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="as_student_set", through="CourseStudent")

    class Meta:
        managed = True
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        constraints = [models.UniqueConstraint(fields=["owner", "code"], name="unique_course")]
        indexes = [models.Index(fields=["owner"])]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Course Teacher"
        verbose_name_plural = "Course Teachers"
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
        verbose_name = "Course Student"
        verbose_name_plural = "Course Students"
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

    class Meta:
        managed = True
        verbose_name = "Project Requirement"
        verbose_name_plural = "Project Requirements"
        constraints = [
            models.CheckConstraint(check=models.Q(from_dt__lte=models.F("to_dt")), name="date_constraint"),
            models.UniqueConstraint(fields=["title", "course"], name="unique_project_requirement"),
        ]

    def __str__(self) -> str:
        from_dt = f"{timezone.localtime(self.from_dt):%Y-%m-%d}"
        to_dt = f"{timezone.localtime(self.to_dt):%Y-%m-%d}"
        return f"{self.course} from {from_dt} to {to_dt}"


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
        indexes = [models.Index(fields=["requirement"])]

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


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
        super().delete(*args, **kwargs)

        # This is the last team student
        if student_count == 1:
            self.team.delete()


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
            ~models.Q(pk=self.pk), email=self.email, course_id=self.course_id, status=self.PENDING
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

            # Show sender full name if its present
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
            ~models.Q(pk=self.pk), email=self.email, team_id=self.team_id, status=self.PENDING
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

            # Show sender full name if its present
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
