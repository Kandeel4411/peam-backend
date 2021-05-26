"""
This module represents the locator config for the courses app
"""

from django.urls import reverse
from .models import Team, Course


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


resources = {
    "team": {"resolver": resolve_team_detail_url, "model": Team},
    "course": {"resolver": resolve_course_detail_url, "model": Course},
}
