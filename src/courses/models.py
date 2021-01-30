import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.utils.tz import local_timezone_now
from users.models import Teacher


class Course(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Teacher, to_field="uid", on_delete=models.CASCADE)
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    code = models.CharField(max_length=10, blank=False, null=False, verbose_name=_("Code"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))

    class Meta:
        managed = True
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        unique_together = [["owner", "code"]]
        indexes = [models.Index(fields=["owner"])]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, to_field="uid", on_delete=models.CASCADE, related_name="courses")
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="teachers")

    class Meta:
        managed = True
        verbose_name = "Course Teacher"
        verbose_name_plural = "Course Teachers"
        unique_together = [["teacher", "course"]]

    def __str__(self) -> str:
        return f"{self.teacher} - {self.course}"


class ProjectRequirement(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="requirements")
    title = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    to_dt = models.DateTimeField(blank=False, verbose_name=_("Deadline"))
    from_dt = models.DateTimeField(default=timezone.now, blank=True, verbose_name=("Start date"))

    class Meta:
        managed = True
        verbose_name = "Project Requirement"
        verbose_name_plural = "Project Requirements"
        unique_together = [["title", "course"]]

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
