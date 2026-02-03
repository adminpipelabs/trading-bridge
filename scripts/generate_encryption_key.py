#!/usr/bin/env python3
"""
Generate Fernet encryption key for ENCRYPTION_KEY environment variable.

Usage:
    python3 scripts/generate_encryption_key.py

Output:
    A base64-encoded Fernet key that should be set as ENCRYPTION_KEY in Railway.

⚠️ IMPORTANT: Back this key up securely. If lost, all encrypted private keys become unrecoverable.
"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("=" * 80)
    print("ENCRYPTION_KEY (copy this value):")
    print("=" * 80)
    print(key.decode())
    print("=" * 80)
    print("\n⚠️  IMPORTANT:")
    print("   1. Copy the key above")
    print("   2. Add it to Railway environment variables as ENCRYPTION_KEY")
    print("   3. Back it up securely (password manager, secure vault, etc.)")
    print("   4. If this key is lost, all encrypted private keys become unrecoverable")
    print("=" * 80)
