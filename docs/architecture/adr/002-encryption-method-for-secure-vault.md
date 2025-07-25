# ADR-002: Encryption Method for Secure Vault

**Date:** 2025-07-25
**Status:** Accepted

## Context
The llm-orchestrator needs to store sensitive information, such as API keys, in a secure vault. We need to choose an encryption method that is both secure and relatively easy to implement and use within our Python application.

## Decision
We will use the `cryptography` library with Fernet symmetric encryption to secure the vault. A user-provided password will be used to derive an encryption key using a key derivation function (KDF) like PBKDF2.

## Consequences
**Positive:**
*   Fernet provides a high-level, easy-to-use API for symmetric authenticated encryption.
*   The `cryptography` library is a well-maintained and widely trusted library for cryptographic operations in Python.
*   Using a KDF adds a layer of security against brute-force attacks on the password.

**Negative:**
*   The security of the vault is still dependent on the strength of the user's password.
*   We need to carefully manage the salt and other parameters for the KDF to ensure security.
