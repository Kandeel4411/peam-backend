class CourseInvitationType:
    """
    Class that represents the possible course invitation types.
    """

    STUDENT_INVITE: str = "student"
    TEACHER_INVITE: str = "teacher"

    INVITE_CHOICES: tuple = ((STUDENT_INVITE, STUDENT_INVITE), (TEACHER_INVITE, TEACHER_INVITE))
    INVITE_LIST: list = [value for value, display in INVITE_CHOICES]
