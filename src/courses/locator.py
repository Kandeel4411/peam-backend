"""
This module represents the locator config for the courses app
"""

from django.urls import reverse
from .models import Team, Course, Project, ProjectRequirement


def resolve_team_detail_url(instance: Team) -> str:
    """
    URL resolver for the course requirement teams
    """
    return reverse(
        "teams-detail",
        kwargs={
            "course_owner": instance.requirement.course.owner.username,
            "course_code": instance.requirement.course.code,
            "requirement_title": instance.requirement.title,
            "team_name": instance.name,
        },
    )


def resolve_course_detail_url(instance: Course) -> str:
    """
    URL resolver for the courses
    """
    return reverse(
        "courses-detail",
        kwargs={
            "course_owner": instance.owner.username,
            "course_code": instance.code,
        },
    )


def resolve_requirement_detail_url(instance: ProjectRequirement) -> str:
    """
    URL resolver for the course requirements
    """
    return reverse(
        "requirements-detail",
        kwargs={
            "course_owner": instance.course.owner.username,
            "course_code": instance.course.code,
            "requirement_title": instance.title,
        },
    )


def resolve_project_detail_url(instance: Project) -> str:
    """
    URL resolver for the course requirement team projects
    """
    return reverse(
        "project-detail",
        kwargs={
            "course_owner": instance.team.requirement.course.owner.username,
            "course_code": instance.team.requirement.course.code,
            "requirement_title": instance.team.requirement.title,
            "team_name": instance.team.name,
            "project_title": instance.title,
        },
    )


resources = {
    "team": {"resolver": resolve_team_detail_url, "model": Team},
    "requirement": {"resolver": resolve_requirement_detail_url, "model": ProjectRequirement},
    "project": {"resolver": resolve_project_detail_url, "model": Project},
    "course": {"resolver": resolve_course_detail_url, "model": Course},
}
