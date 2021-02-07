import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import CICharField

from core.utils.tz import local_timezone_now

User = get_user_model()


class Course(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, to_field="uid", on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    code = CICharField(max_length=10, blank=False, null=False, verbose_name=_("Code"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    teachers = models.ManyToManyField(User, related_name="as_teacher_set", through="CourseTeacher")
    students = models.ManyToManyField(User, related_name="as_student_set", through="CourseStudent")

    class Meta:
        managed = True
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        constraints = [models.UniqueConstraint(fields=["owner", "code"], name="unique_course")]
        indexes = [models.Index(fields=["owner"])]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(User, to_field="uid", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Course Teacher"
        verbose_name_plural = "Course Teachers"
        constraints = [models.UniqueConstraint(fields=["course", "teacher"], name="unique_course_Teacher")]

    def __str__(self) -> str:
        return f"{self.teacher} - {self.course}"


class CourseStudent(models.Model):
    student = models.ForeignKey(User, to_field="uid", on_delete=models.CASCADE)
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
    students = models.ManyToManyField(User, related_name="teams", through="TeamStudent")

    class Meta:
        managed = True
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        constraints = [models.UniqueConstraint(fields=["name", "requirement"], name="unique_team")]

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


class TeamStudent(models.Model):
    student = models.ForeignKey(User, to_field="uid", on_delete=models.CASCADE)
    team = models.ForeignKey(Team, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Team Student"
        verbose_name_plural = "Team Students"
        constraints = [models.UniqueConstraint(fields=["student", "team"], name="unique_team_student")]

    def __str__(self) -> str:
        return f"{self.student} - {self.team}"
