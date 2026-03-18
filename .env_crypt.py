#!/usr/bin/env python3
"""
.env file encryption/decryption utility.
Encrypts variable values (not keys) with password-based encryption.
Handles both root .env and frontend/.env files.

Usage:
    python .env_crypt.py encrypt   # Encrypt .env → .env.encrypted (both root and frontend)
    python .env_crypt.py decrypt   # Decrypt .env.encrypted → .env (both root and frontend)
"""

import sys
import os
from pathlib import Path
from getpass import getpass
import base64
import hashlib

from cryptography.fernet import Fernet


# .env files to encrypt/decrypt
ENV_FILES = [
    '.env',                    # Root .env
    'frontend/.env',           # Frontend .env
]


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte key from password + salt using PBKDF2."""
    key_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt,
        100_000,  # iterations
        dklen=32
    )
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_env(env_path: str, password: str, output_path: str) -> None:
    """Encrypt .env file values. Format: KEY=ENC[base64_salt:base64_ciphertext]"""
    if not os.path.exists(env_path):
        print(f"⚠️  Skipped (not found): {env_path}")
        return

    lines = Path(env_path).read_text().strip().split('\n')
    encrypted_lines = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            encrypted_lines.append(line)
            continue

        if '=' not in line:
            encrypted_lines.append(line)
            continue

        key, value = line.split('=', 1)
        
        # Generate a random salt for each value
        salt = os.urandom(16)
        derived_key = derive_key_from_password(password, salt)
        cipher = Fernet(derived_key)
        ciphertext = cipher.encrypt(value.encode())
        
        # Format: KEY=ENC[salt:ciphertext] (base64 encoded)
        salt_b64 = base64.b64encode(salt).decode()
        cipher_b64 = base64.b64encode(ciphertext).decode()
        encrypted_value = f"ENC[{salt_b64}:{cipher_b64}]"
        
        encrypted_lines.append(f"{key}={encrypted_value}")

    Path(output_path).write_text('\n'.join(encrypted_lines) + '\n')
    print(f"✅ Encrypted: {env_path} → {output_path}")


def decrypt_env(env_path: str, password: str, output_path: str) -> None:
    """Decrypt .env.encrypted file back to plaintext .env"""
    if not os.path.exists(env_path):
        print(f"⚠️  Skipped (not found): {env_path}")
        return

    lines = Path(env_path).read_text().strip().split('\n')
    decrypted_lines = []
    failed = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            decrypted_lines.append(line)
            continue

        if '=' not in line:
            decrypted_lines.append(line)
            continue

        key, value = line.split('=', 1)
        
        if not value.startswith('ENC[') or not value.endswith(']'):
            decrypted_lines.append(line)
            continue

        # Extract salt and ciphertext
        try:
            inner = value[4:-1]  # Remove ENC[ and ]
            salt_b64, cipher_b64 = inner.split(':', 1)
            salt = base64.b64decode(salt_b64)
            ciphertext = base64.b64decode(cipher_b64)
            
            derived_key = derive_key_from_password(password, salt)
            cipher = Fernet(derived_key)
            plaintext = cipher.decrypt(ciphertext).decode()
            
            decrypted_lines.append(f"{key}={plaintext}")
        except Exception as e:
            print(f"❌ Failed to decrypt {key}: {e}")
            failed = True
            decrypted_lines.append(line)

    if failed:
        print("⚠️  Some values could not be decrypted (wrong password?)")
        sys.exit(1)

    Path(output_path).write_text('\n'.join(decrypted_lines) + '\n')
    print(f"✅ Decrypted: {env_path} → {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    
    if command == 'encrypt':
        print("🔐 Encrypting .env files...")
        
        password = getpass("Enter encryption password: ")
        confirm = getpass("Confirm password: ")
        
        if password != confirm:
            print("❌ Error: Passwords don't match")
            sys.exit(1)
        
        if len(password) < 8:
            print("❌ Error: Password must be at least 8 characters")
            sys.exit(1)
        
        for env_file in ENV_FILES:
            encrypted_file = f"{env_file}.encrypted"
            encrypt_env(env_file, password, encrypted_file)
        
        print("\n📝 Next steps:")
        print("   1. Add to .gitignore:")
        for env_file in ENV_FILES:
            print(f"      {env_file}")
        print("   2. Commit the .encrypted files:")
        for env_file in ENV_FILES:
            print(f"      git add {env_file}.encrypted")
        
    elif command == 'decrypt':
        print("🔓 Decrypting .env files...")
        
        password = getpass("Enter decryption password: ")
        
        for env_file in ENV_FILES:
            encrypted_file = f"{env_file}.encrypted"
            decrypt_env(encrypted_file, password, env_file)
        
        print("\n📝 Keep these in .gitignore:")
        for env_file in ENV_FILES:
            print(f"   {env_file}")
        
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()

