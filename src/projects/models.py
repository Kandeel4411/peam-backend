from django.db import models
from django.utils.translation import gettext_lazy as _

from courses.models import ProjectRequirement
from users.models import Student


class Team(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name=_("Name"))
    requirement = models.ForeignKey(ProjectRequirement, on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        unique_together = [["name", "requirement"]]

    def __str__(self) -> str:
        return f"{self.name} - {self.requirement}"


class TeamMember(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        managed = True
        verbose_name = "Team member"
        verbose_name_plural = "Team members"
        unique_together = [["student", "team"]]

    def __str__(self) -> str:
        return f"{self.student} - {self.team}"
