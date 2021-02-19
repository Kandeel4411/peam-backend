class InvitationStatus:
    """
    Class that represents the possible invitation statuses.
    """

    PENDING: str = "Pending"
    ACCEPTED: str = "Accepted"
    REJECTED: str = "Rejected"
    EXPIRED: str = "Expired"

    STATUS_CHOICES: tuple = (
        (PENDING, PENDING),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
        (EXPIRED, EXPIRED),
    )
    STATUS_LIST: list = [value for value, display in STATUS_CHOICES]
