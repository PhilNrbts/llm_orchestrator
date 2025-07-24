# Core Concepts

This project is built on a few core concepts that are important to understand.

## Security: The Encrypted Vault

Your API keys are sensitive credentials. To keep them safe, we use an encrypted vault (`vault.enc`).

-   **Encryption**: The vault is encrypted using Fernet (AES-128-CBC).
-   **Master Password**: A single master password is used to derive an encryption key. This password is the only way to unlock the vault.
-   **In-Memory Decryption**: The vault is only ever decrypted in memory when a command is run. Your keys are never written to disk in plaintext.

## Configuration Files

The CLI is controlled by two main YAML files:

-   `models.yaml`: Defines the models available to the orchestrator, their settings (like `temperature`), and the available `roles` and `personas` for autocompletion.
-   `config.yaml`: Stores your saved chains. You can edit this file directly or manage it using the `my-cli chain save` command.

## Session Management

To avoid requiring your master password for every single command, the CLI uses a temporary, encrypted session file (`.session_cache`).

-   When you run `my-cli auth start`, your password is encrypted and stored in this file.
-   For the next 15 minutes, other commands can decrypt this file to get your password.
-   After 15 minutes of inactivity, the session file is considered expired and will be deleted.
-   Running `my-cli auth stop` will also delete the file immediately.
