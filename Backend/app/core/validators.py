# app/core/validators.py
import re
from app.core.config import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE,
    PASSWORD_REQUIRE_NUMBERS,
    PASSWORD_REQUIRE_SYMBOLS,
    PHONE_PREFIX,
    PHONE_PATTERN,
    VALID_DISTRICTS
)


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_password(password: str) -> bool:
    """
    Validate password against strong requirements:
    - Minimum length
    - Uppercase letter
    - Lowercase letter
    - Number
    - Special symbol
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )

    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number")

    if PASSWORD_REQUIRE_SYMBOLS and not re.search(r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>?/\\|`~]", password):
        raise ValidationError("Password must contain at least one special character (!@#$%^&*)")

    return True


def validate_phone_number(phone: str) -> bool:
    """Validate Sri Lankan phone number format (+94 prefix, 9 digits)"""
    if not re.match(PHONE_PATTERN, phone):
        raise ValidationError(
            f"Phone number must follow format: {PHONE_PREFIX}XXXXXXXXX (9 digits after {PHONE_PREFIX})"
        )
    return True


def validate_district(district: str) -> bool:
    """Validate district against Sri Lankan districts whitelist"""
    if district and district not in VALID_DISTRICTS:
        raise ValidationError(
            f"Invalid district. Must be one of: {', '.join(VALID_DISTRICTS)}"
        )
    return True


def validate_user_registration(user_data: dict) -> bool:
    """Validate all user registration fields"""
    # Validate password
    validate_password(user_data.get("password", ""))

    # Validate phone number
    validate_phone_number(user_data.get("phoneNumber", ""))

    # Validate district if provided
    if user_data.get("district"):
        validate_district(user_data["district"])

    return True
