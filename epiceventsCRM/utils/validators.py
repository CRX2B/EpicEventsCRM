import re


def is_valid_email_format(email: str) -> bool:
    """Vérifie un format d'email basique."""
    if not isinstance(email, str):
        return False
    if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return True
    return False


def is_valid_phone_format(phone: str) -> bool:
    """Vérifie un format de téléphone simple (chiffres, espaces, +, -)."""
    if not isinstance(phone, str):
        return False
    if re.match(r"^\+?[\d\s-]{7,20}$", phone):
        cleaned_phone = phone.replace(" ", "").replace("-", "")
        if not cleaned_phone:
            return False
        if cleaned_phone.startswith("+"):
            return cleaned_phone[1:].isdigit()
        else:
            return cleaned_phone.isdigit()
    return False
