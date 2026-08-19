from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet:
    """Returns a Fernet instance using the configured ENCRYPTION_KEY."""
    return Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))

def encrypt(plaintext: str) -> str:
    """Encrypts plaintext string and returns ciphertext as string."""
    if not plaintext:
        return plaintext
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt(ciphertext: str) -> str:
    """Decrypts ciphertext string and returns plaintext as string."""
    if not ciphertext:
        return ciphertext
    f = get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
