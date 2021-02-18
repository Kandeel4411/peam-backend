import uuid
from typing import Optional

from django.db import models, transaction
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

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


class TeamStudent(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, to_field="uid", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, to_field="uid", on_delete=models.CASCADE)

    def validate_unique(self, *args, **kwargs) -> None:
        """
        Custom validate unique method
        """
        super().validate_unique(*args, **kwargs)

        # Enforcing that student can only belong to one team in each project requirement
        if self.__class__.objects.filter(student=self.student, team__requirement=self.team.requirement).exists():
            raise ValidationError(
                message=f"{self.__class__} with this (student, requirement) already exists.",
            )

    class Meta:
        managed = True
        verbose_name = "Team Student"
        verbose_name_plural = "Team Students"
        constraints = [models.UniqueConstraint(fields=["student", "team"], name="unique_team_student")]

    def __str__(self) -> str:
        return f"{self.student} - {self.team}"


class CourseInvitation(BaseInvitation):
    STUDENT_INVITE: str = "student"
    TEACHER_INVITE: str = "teacher"

    INVITE_CHOICES: tuple = ((STUDENT_INVITE, STUDENT_INVITE), (TEACHER_INVITE, TEACHER_INVITE))

    email = models.EmailField(blank=False, null=False, unique=True, verbose_name=_("Email address"))
    type = models.CharField(choices=INVITE_CHOICES, max_length=30, blank=False, null=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="invitations")

    class Meta(BaseInvitation.Meta):
        abstract = False
        managed = True
        verbose_name = "Course Invitation"
        verbose_name_plural = "Course Invitations"
        constraints = BaseInvitation.Meta.constraints + [
            models.UniqueConstraint(fields=["email", "type", "course"], name="unique_course_invitation")
        ]

    def __str__(self) -> str:
        return f"{self.sender} invited {self.email}[{self.type}] to {self.course}"

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

        :*args, **kwargs: arguments that are going to be directly passed to ORM object creation

        *Note:* This method should generally be used instead of manual creation of course invitation as
        it ensures that if creation fails, an email wont be sent and vice versa
        """

        adapter = get_adapter(request)
        site = get_current_site(request)
        protocol: str = settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL
        invite_url: str = f"{protocol}://{site.domain}{reverse('login')}"

        with transaction.atomic():
            invitation: cls = cls.objects.create(*args, **kwargs)

            # Adding Invitation token as a query param to the invite url
            invite_url += f"?{settings.FRONTEND_INVITATION_TOKEN_PARAM}={invitation.token}"

            # Show sender full name if its present
            sender = invitation.sender
            if sender.full_name is None:
                sender = sender.username
            else:
                sender = sender.full_name.title()

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
