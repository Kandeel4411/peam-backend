import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import ProjectRequirement
from users.models import Student


class Team(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Name"))
    requirement = models.ForeignKey(ProjectRequirement, to_field="uid", on_delete=models.CASCADE, related_name="teams")

    class Meta:
        managed = True
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        unique_together = [["name", "requirement"]]

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


class TeamMember(models.Model):
    student = models.ForeignKey(Student, to_field="uid", on_delete=models.CASCADE, related_name="teams")
    team = models.ForeignKey(Team, to_field="uid", on_delete=models.CASCADE, related_name="members")

    class Meta:
        managed = True
        verbose_name = "Team member"
        verbose_name_plural = "Team members"
        unique_together = [["student", "team"]]

    def __str__(self) -> str:
        return f"{self.student} - {self.team}"
