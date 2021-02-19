from django.utils.crypto import get_random_string


def generate_token() -> str:
    """
    Helper function that generates a new invitation token
    """
    return get_random_string(64)
