# Getting Started

This guide will walk you through the process of installing and configuring the LLM Orchestrator CLI.

## 1. Installation

First, you'll need to have [Poetry](https://python-poetry.org/docs/#installation) installed. Once you have Poetry, you can install the application with the following command:

```bash
poetry install
```

## 2. Initializing the Vault

The first time you run the application, you'll need to initialize the vault. The vault is an encrypted file that stores your API keys. To initialize the vault, run the following command:

```bash
poetry run python -m scripts.init_vault
```

You will be prompted to create a master password. This password will be used to encrypt and decrypt your API keys.

## 3. Adding API Keys

After you've initialized the vault, you'll need to add your API keys. You can do this by running the `vault_manager.py` script:

```bash
poetry run python -m scripts.vault_manager
```

You will be prompted for your master password, and then you will be able to add, update, or delete API keys.

## 4. Running the Application

Once you've added your API keys, you can run the application with the following command:

```bash
poetry run python -m app.main
```

You will be prompted for your master password, and then you will be dropped into the interactive chat.

### Bypassing the Password Prompt

If you are in an environment where the password prompt is not supported, you can use the `--no-mask` flag:

```bash
poetry run python -m app.main --no-mask
```
