import base64
import hashlib

from django.conf import settings


PREFIX = "enc::"


def _fernet():
    from cryptography.fernet import Fernet

    source = (getattr(settings, "DATA_ENCRYPTION_KEY", "") or settings.SECRET_KEY).encode("utf-8")
    key_bytes = hashlib.sha256(source).digest()
    token = base64.urlsafe_b64encode(key_bytes)
    return Fernet(token)


def encrypt_value(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    if value.startswith(PREFIX):
        return value
    encrypted = _fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{PREFIX}{encrypted}"


def decrypt_value(stored_value: str) -> str:
    value = (stored_value or "").strip()
    if not value:
        return ""
    if not value.startswith(PREFIX):
        return value
    token = value[len(PREFIX) :].encode("utf-8")
    try:
        return _fernet().decrypt(token).decode("utf-8")
    except Exception:
        return ""
