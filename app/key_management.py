import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

VAULT_FILE_PATH = os.environ.get("VAULT_FILE_PATH", "vault.enc")
PASSWORD_SALT = b"a-secure-random-salt-should-be-used-here"


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a stable encryption key from a password."""
    kdf = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, 32)
    return base64.urlsafe_b64encode(kdf)


def get_api_keys(password: str) -> dict[str, str]:
    """Decrypt the vault and return API keys."""
    vault_path = os.environ.get("VAULT_FILE_PATH", "vault.enc")
    if not os.path.exists(vault_path):
        raise FileNotFoundError(
            f"Vault file not found at {vault_path}. Please run init_vault.py."
        )
    try:
        with open(vault_path, "rb") as f:
            encrypted_data = f.read()

        encryption_key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(encryption_key)
        decrypted_data = cipher.decrypt(encrypted_data).decode("utf-8")

        keys = dict(line.split("=", 1) for line in decrypted_data.splitlines() if line)
        return keys
    except InvalidToken:
        raise ValueError("Invalid password or corrupted vault.")
    except Exception as e:
        raise RuntimeError(f"Failed to decrypt vault: {e}")
