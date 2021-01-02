import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Attachment
from core.utils.tz import local_timezone_now
from users.models import Teacher


class Course(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name=_("Title"))
    code = models.CharField(max_length=10, unique=True, blank=False, null=False, verbose_name=_("Code"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))

    class Meta:
        managed = True
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class CourseTeacher(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, to_field="uid", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="teacher")

    class Meta:
        managed = True
        verbose_name = "Course Teacher"
        verbose_name_plural = "Course Teachers"
        unique_together = [["teacher", "course"]]

    def __str__(self) -> str:
        return f"{self.teacher} - {self.course}"


class ProjectRequirement(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="requirement")
    title = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name=_("Title"))
    description = models.CharField(max_length=300, blank=True, null=False, verbose_name=_("Description"))
    to_dt = models.DateTimeField(blank=False, verbose_name=_("Deadline"))
    from_dt = models.DateTimeField(default=timezone.now, blank=True, verbose_name=("Start date"))

    class Meta:
        managed = True
        verbose_name = "Project Requirement"
        verbose_name_plural = "Project Requirements"

    def __str__(self) -> str:
        from_dt = f"{timezone.localtime(self.from_dt):%Y-%m-%d}"
        to_dt = f"{timezone.localtime(self.to_dt):%Y-%m-%d}"
        return f"{self.course} from {from_dt} to {to_dt}"


class CourseAttachment(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, to_field="uid", on_delete=models.CASCADE, related_name="attachment")
    attachment = models.ForeignKey(Attachment, to_field="uid", on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Course Attachment"
        verbose_name_plural = "Course Attachments"

    def __str__(self) -> str:
        return f"{self.course.code}: {self.attachment}"
