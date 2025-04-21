import pytest

from epiceventsCRM.utils.validators import is_valid_email_format, is_valid_phone_format


@pytest.mark.parametrize(
    "email, expected",
    [
        ("test@example.com", True),
        ("test.lastname@example.co.uk", True),
        ("test+alias@example.com", True),
        ("test@", False),
        ("test@domain", False),
        ("@domain.com", False),
        ("test domain.com", False),
        (12345, False),
        (None, False),
        ("", False),
    ],
)
def test_is_valid_email_format(email, expected):
    assert is_valid_email_format(email) == expected


@pytest.mark.parametrize(
    "phone, expected",
    [
        ("1234567", True),
        ("+33612345678", True),
        ("01 23 45 67 89", True),
        ("01-23-45-67-89", True),
        ("+33 1 23 45 67 89", True),
        ("123456", False),
        ("abcdefg", False),
        ("123 456+", False),
        ("+123 456 7890 123 456 78901", False),
        (123456789, False),
        (None, False),
        ("", False),
        ("+", False),
        ("-", False),
        (" ", False),
        (" + ", False),
        (" - ", False),
    ],
)
def test_is_valid_phone_format(phone, expected):
    assert is_valid_phone_format(phone) == expected
