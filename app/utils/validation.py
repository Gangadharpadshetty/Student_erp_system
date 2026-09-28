import re

from fastapi import HTTPException

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9().\-\s]+$")


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    return normalized


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must contain at least 8 characters")
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="Password must be no longer than 72 bytes")
    return password


def validate_phone(phone: str) -> str:
    normalized = phone.strip()
    digit_count = sum(character.isdigit() for character in normalized)
    if not PHONE_PATTERN.fullmatch(normalized) or not 7 <= digit_count <= 15:
        raise HTTPException(status_code=422, detail="Enter a phone number with 7 to 15 digits")
    return normalized