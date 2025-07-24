import getpass
import os
import hashlib
import base64
from cryptography.fernet import Fernet

VAULT_FILE = "vault.enc"
# In a real production system, this salt should be managed securely
# and not hardcoded. For this project, it's set here for simplicity.
PASSWORD_SALT = b"a-secure-random-salt-should-be-used-here"

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a stable encryption key from a password."""
    kdf = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,  # Recommended iterations
        32
    )
    return base64.urlsafe_b64encode(kdf)

def main():
    """Main function to create and encrypt the API key vault."""
    print("--- Secure API Key Vault Setup ---")
    if os.path.exists(VAULT_FILE):
        overwrite = input(f"Warning: '{VAULT_FILE}' already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Vault setup cancelled.")
            return

    keys = {
        "ANTHROPIC_API_KEY": getpass.getpass("Enter Anthropic API Key: "),
        "GEMINI_API_KEY": getpass.getpass("Enter Gemini API Key: "),
        "DEEPSEEK_API_KEY": getpass.getpass("Enter DeepSeek API Key: "),
        "MISTRAL_API_KEY": getpass.getpass("Enter Mistral API Key: ")
    }

    password = getpass.getpass("Set a master password for the vault: ")
    confirm_password = getpass.getpass("Confirm master password: ")

    if password != confirm_password:
        print("\nError: Passwords do not match. Aborting.")
        exit(1)
    
    if not password:
        print("\nError: Password cannot be empty. Aborting.")
        exit(1)

    # Prepare data for encryption
    env_content = "\n".join(f"{key}={value}" for key, value in keys.items())

    # Encrypt and store
    try:
        encryption_key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(encryption_key)
        encrypted_data = cipher.encrypt(env_content.encode('utf-8'))

        with open(VAULT_FILE, "wb") as f:
            f.write(encrypted_data)
        
        print(f"\nSuccess! API keys encrypted and saved to '{VAULT_FILE}'.")
        print("Keep your master password safe. It is not recoverable.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during encryption: {e}")

if __name__ == "__main__":
    main()
