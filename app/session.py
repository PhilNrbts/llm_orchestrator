import json
import os
import time

from cryptography.fernet import Fernet

# Simple file-based session management
SESSION_FILE = ".session_cache"
SESSION_TIMEOUT_SECONDS = 15 * 60  # 15 minutes


def start_session(password: str):
    """Encrypt and save the password to a session file."""
    key = Fernet.generate_key()
    cipher = Fernet(key)

    session_data = {
        "timestamp": time.time(),
        "key": key.decode("utf-8"),
        "password_enc": cipher.encrypt(password.encode("utf-8")).decode("utf-8"),
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)
    os.chmod(SESSION_FILE, 0o600)  # Restrict permissions


def stop_session():
    """Remove the session file."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


def get_password_from_session() -> str | None:
    """
    Retrieve the password from the session if it's valid and not expired.
    """
    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(SESSION_FILE) as f:
            session_data = json.load(f)

        timestamp = session_data.get("timestamp", 0)
        if time.time() - timestamp > SESSION_TIMEOUT_SECONDS:
            stop_session()
            return None

        key = session_data.get("key", "").encode("utf-8")
        password_enc = session_data.get("password_enc", "").encode("utf-8")

        cipher = Fernet(key)
        password = cipher.decrypt(password_enc).decode("utf-8")
        return password

    except (json.JSONDecodeError, KeyError, Exception):
        # If file is corrupted or invalid, clean up
        stop_session()
        return None
