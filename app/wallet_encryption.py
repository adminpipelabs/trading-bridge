"""
Wallet encryption utilities for Solana bot private keys.
Uses Fernet symmetric encryption (AES 128 in CBC mode).
"""

import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# Initialize Fernet cipher
_fernet = None
if ENCRYPTION_KEY:
    try:
        _fernet = Fernet(ENCRYPTION_KEY.encode())
    except Exception as e:
        logger.error(f"Failed to initialize Fernet encryption: {e}")
        _fernet = None
else:
    logger.warning("ENCRYPTION_KEY not set - wallet encryption will not work")


def encrypt_private_key(private_key: str) -> str:
    """
    Encrypt a Solana private key (base58 string).
    
    Args:
        private_key: Base58 encoded private key string
        
    Returns:
        Encrypted private key as base64 string
        
    Raises:
        RuntimeError: If encryption key is not configured
    """
    if not _fernet:
        raise RuntimeError("ENCRYPTION_KEY not set. Cannot encrypt private keys.")
    
    try:
        encrypted = _fernet.encrypt(private_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Failed to encrypt private key: {e}")
        raise RuntimeError(f"Encryption failed: {e}")


def decrypt_private_key(encrypted_key: str) -> str:
    """
    Decrypt a Solana private key.
    
    Args:
        encrypted_key: Encrypted private key (base64 string)
        
    Returns:
        Decrypted private key as base58 string
        
    Raises:
        RuntimeError: If decryption fails or key not configured
    """
    if not _fernet:
        raise RuntimeError("ENCRYPTION_KEY not set. Cannot decrypt private keys.")
    
    try:
        decrypted = _fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt private key: {e}")
        raise RuntimeError(f"Decryption failed: {e}")
