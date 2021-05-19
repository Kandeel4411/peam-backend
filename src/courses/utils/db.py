from typing import Optional

from ..models import (
    CourseStudent,
    CourseTeacher,
    TeamStudent,
)


def is_course_owner(user, course_id: Optional = None, code: Optional[str] = None) -> bool:
    """
    Checks if user is the course owner.

    :param course_id: the uuid of the course ( will always be used instead of other parameters if given)

    :param code: the code of the course ( if course_id wasn't given then this will be used
    with the user to identify the course)

    :param user: User object that the check will be applied to.
    """
    if course_id is not None:
        return user.courses_owned.filter(uid=course_id).exists()
    else:
        return user.courses_owned.filter(code=code).exists()


def is_course_student(
    user, course_id: Optional = None, owner_username: Optional[str] = None, code: Optional[str] = None
) -> bool:
    """
    Checks if user is a course student.

    :param course_id: the uuid of the course ( will always be used instead of code if given)

    :param code: the code of the course ( if course_id wasn't given then this will be used
    with the owner's username to identify the course)
    :param owner_username: the username of the owner

    :param user: User object that the check will be applied to.
    """
    if course_id is not None:
        return CourseStudent._default_manager.filter(student_id=user.uid, course_id=course_id).exists()
    else:
        return CourseStudent._default_manager.filter(
            student_id=user.uid, course__owner__username=owner_username, course__code=code
        ).exists()


def is_course_teacher(
    user, course_id: Optional = None, owner_username: Optional[str] = None, code: Optional[str] = None
) -> bool:
    """
    Checks if user is a course teacher.

    :param course_id: the uuid of the course ( will always be used instead of other parameters if given)

    :param code: the code of the course ( if course_id wasn't given then this will be used
    with the owner's username to identify the course)
    :param owner_username: the username of the owner

    :param user: User object that the check will be applied to.
    """
    if course_id is not None:
        return CourseTeacher._default_manager.filter(teacher_id=user.uid, course_id=course_id).exists()
    else:
        return CourseTeacher._default_manager.filter(
            teacher_id=user.uid, course__owner__username=owner_username, course__code=code
        ).exists()


def is_team_student(
    user,
    team_id: Optional = None,
    owner_username: Optional[str] = None,
    code: Optional[str] = None,
    requirement_title: Optional[str] = None,
) -> bool:
    """
    Checks if user is a team student.

    :param team_id: the uuid of the team ( will always be used instead of other parameters if given)

    :param code: the code of the team ( if team_id wasn't given then this will be used
    with the owner's username and requirement title to identify the team)
    :param owner_username: the username of the owner
    :param requirement_title: the title of the project requirement

    :param user: User object that the check will be applied to.
    """
    if team_id is not None:
        return TeamStudent._default_manager.filter(team_id=team_id, student_id=user.uid).exists()
    else:
        return TeamStudent._default_manager.filter(
            team__requirement__course__owner__username=owner_username,
            team__requirement__course__code=code,
            team__requirement__title=requirement_title,
            student_id=user.uid,
        ).exists()
