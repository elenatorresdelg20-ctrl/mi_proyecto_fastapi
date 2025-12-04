from typing import Optional
import os

try:
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - cryptography optional
    Fernet = None

from .settings import FERNET_KEY


def get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance if `FERNET_KEY` is configured and cryptography is available."""
    if not FERNET_KEY:
        return None
    if Fernet is None:
        raise RuntimeError("cryptography package is required to use Fernet encryption")
    try:
        return Fernet(FERNET_KEY.encode())
    except Exception as e:
        raise RuntimeError(f"Invalid FERNET_KEY: {e}")


def encrypt_value(plain: str) -> str:
    f = get_fernet()
    if not f:
        raise RuntimeError("FERNET_KEY not configured; cannot encrypt")
    return f.encrypt(plain.encode()).decode()


def decrypt_value(token: str) -> str:
    f = get_fernet()
    if not f:
        raise RuntimeError("FERNET_KEY not configured; cannot decrypt")
    return f.decrypt(token.encode()).decode()
