import re

def verify_email(email: str) -> bool:
    """Verify if the email is in a valid format."""
    email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return bool(email_regex.match(email))

def verify_password(password: str) -> bool:
    """
    Verify if the password meets the requirements:
    - At least 8 characters long
    - Alphanumeric
    - At least one capital letter
    """
    if len(password) < 8:
        return False
    if not password.isalnum():
        return False
    if not any(c.isupper() for c in password):
        return False
    return True
