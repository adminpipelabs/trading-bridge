"""
Wallet Encryption Module
Encrypts and decrypts private keys using Fernet symmetric encryption.
"""
import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = None

def _ensure_fernet():
    """Lazy initialization of Fernet - only fails when actually needed."""
    global fernet
    if fernet is not None:
        return fernet
    
    if not ENCRYPTION_KEY:
        logger.error("ENCRYPTION_KEY environment variable not set!")
        logger.error("Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        raise ValueError("ENCRYPTION_KEY environment variable must be set")
    
    try:
        fernet = Fernet(ENCRYPTION_KEY.encode())
        return fernet
    except Exception as e:
        logger.error(f"Failed to initialize Fernet with ENCRYPTION_KEY: {e}")
        raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")

# Initialize if key is available (for backward compatibility)
if ENCRYPTION_KEY:
    try:
        fernet = Fernet(ENCRYPTION_KEY.encode())
    except Exception as e:
        logger.warning(f"Failed to initialize Fernet at import time: {e}. Will retry on use.")


def encrypt_private_key(private_key: str) -> str:
    """
    Encrypt a private key using Fernet.
    
    Args:
        private_key: Plain text private key (base58 encoded)
    
    Returns:
        Encrypted private key (base64 encoded)
    """
    try:
        _ensure_fernet()
        encrypted = fernet.encrypt(private_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Failed to encrypt private key: {e}")
        raise


def decrypt_private_key(encrypted_key: str) -> str:
    """
    Decrypt a private key using Fernet.
    
    Args:
        encrypted_key: Encrypted private key (base64 encoded)
    
    Returns:
        Decrypted private key (base58 encoded)
    """
    try:
        _ensure_fernet()
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt private key: {e}")
        raise
