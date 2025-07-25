# llm-orchestrator

A powerful, local-first command-line tool for orchestrating queries to multiple Large Language Models (LLMs), managed with Poetry.

## Quick Start

1.  **Install Poetry**: Follow the [official instructions](https://python-poetry.org/docs/#installation) to install Poetry.
2.  **Install Dependencies**:
    ```bash
    poetry install
    ```
3.  **Run Commands**:
    ```bash
    # Run the main CLI
    poetry run python -m app.main --help

    # Run the settings manager
    poetry run python settings.py
    ```

## Documentation

For full documentation, please see the `docs/` directory.

## Roadmap

The future plans for this project are outlined in the [ROADMAP.md](ROADMAP.md) file.

---
# Project Summary
## Architecture
### 000-template.md
# ADR-00X: [Title of ADR]

**Date:** [YYYY-MM-DD]
**Status:** [Proposed | Accepted | Deprecated | Superseded]

## Context
[Describe the problem or the need for a decision.]

## Decision
[State the decision that was made.]

## Consequences
[Outline the positive and negative results of this decision.]


---

### 001-choice-of-click-for-cli.md
# ADR-001: Choice of Click for CLI

**Date:** 2025-07-25
**Status:** Accepted

## Context
The project requires a robust and user-friendly command-line interface (CLI). We considered several Python libraries for this purpose, including `argparse`, `docopt`, and `click`. The primary requirements were ease of use for developers, good out-of-the-box help generation, and extensibility for future features.

## Decision
We have chosen to use `click` as the framework for our CLI.

## Consequences
**Positive:**
*   `click` provides a simple and intuitive API for creating commands and options.
*   Automatic help page generation is clear and well-formatted.
*   The decorator-based approach keeps the CLI logic clean and separate from the core application logic.
*   `click` is highly extensible and has a rich ecosystem of plugins.

**Negative:**
*   `click` adds an external dependency to the project.
*   For very simple CLIs, `click` might be considered overkill compared to the standard `argparse`.


---

### 002-encryption-method-for-secure-vault.md
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


---

### c1-system-context.md
# C1: System Context

This diagram shows the system context for the llm-orchestrator.

![System Context Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## Users

*   **Developer:** A software developer who uses the llm-orchestrator to interact with various LLMs.

## System

*   **llm-orchestrator:** The command-line tool that provides the core functionality.

## External Dependencies

*   **LLM Providers:** External services like OpenAI, Anthropic, etc., that provide the language models.
*   **Configuration Files:** Local files that store settings and API keys.
*   **Secure Vault:** An encrypted local file for storing sensitive data.


---

### c2-container-diagram.md
# C2: High-Level Components Diagram

This diagram shows the major high-level components within the llm-orchestrator system.

*(Note: In the C4 model, these are called "Containers," but we are using the term "High-Level Components" to avoid confusion with Docker containers.)*

![Component Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## High-Level Components

*   **CLI App:** The main command-line interface application that users interact with.
*   **Vault:** The secure, encrypted file that stores API keys and other sensitive data.
*   **Config Files:** The YAML files that store the application's configuration.
*   **Orchestration Engine:** The core component that manages interactions with LLMs.
*   **LLM Clients:** The individual clients for each supported LLM provider.


---

### c3-component-diagram.md
# C3: Component Diagram

This diagram shows the components within the CLI App container.

![Component Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## Components

*   **Main (main.py):** The entry point for the CLI application. It uses `click` to define the commands and options.
*   **Orchestrator (orchestrator.py):** This component is responsible for managing the overall workflow. It takes a user's query, determines which LLMs to use, and whether to run them in parallel or sequentially.
*   **LLM Clients (clients.py):** This module contains the individual clients for each LLM provider (e.g., OpenAI, Anthropic). Each client is responsible for making the actual API calls to the provider.
*   **Key Management (key_management.py):** This component interacts with the secure vault to retrieve and manage API keys.
*   **Session (session.py):** This component manages the user's session, including loading configuration and handling conversation history.
*   **Chat (chat.py):** This component provides the interactive chat functionality.


---

## Other Documents
### README.md
# llm-orchestrator

A powerful, local-first command-line tool for orchestrating queries to multiple Large Language Models (LLMs), managed with Poetry.

## Quick Start

1.  **Install Poetry**: Follow the [official instructions](https://python-poetry.org/docs/#installation) to install Poetry.
2.  **Install Dependencies**:
    ```bash
    poetry install
    ```
3.  **Run Commands**:
    ```bash
    # Run the main CLI
    poetry run python -m app.main --help

    # Run the settings manager
    poetry run python settings.py
    ```

## Documentation

For full documentation, please see the `docs/` directory.

## Roadmap

The future plans for this project are outlined in the [ROADMAP.md](ROADMAP.md) file.

---

### contributing.md
# Contributing

We welcome contributions to the llm-orchestrator!

## Development

To get started with development, you will need to install the project and its dependencies using Poetry.

```bash
poetry install
```

## Code Style

We use `black` for code formatting and `ruff` for linting. Please make sure your code conforms to these standards before submitting a pull request.

```bash
poetry run black .
poetry run ruff check .
```

## Proposing Changes

Any major architectural changes should be proposed as an Architecture Decision Record (ADR). Please see the `docs/architecture/adr` directory for more information.


---

### future-development.md
# Future Development Ideas

This document contains a more detailed and technical breakdown of potential future features and improvements for the llm-orchestrator. It serves as a supplement to the high-level `ROADMAP.md`.

## 1. Modular Home Directory System

**Target Location:** `~/.config/llm-orchestrator/`, `~/.local/share/llm-orchestrator/`

- __XDG Base Directory Compliance__: Cross-platform standard directories
- __Configuration Hierarchy__: System → User → Project level configurations
- __Profile Management__: Multiple user profiles with separate vaults
- __Migration Tools__: Automatic config migration between versions

## 2. Advanced Chain Architecture

**Target Location:** `app/chains/`, `app/workflows/`

- __Chain Definition Language__: YAML-based workflow descriptions
- __Conditional Logic__: If/then branching based on response analysis
- __Loop Constructs__: Iterative refinement with convergence criteria
- __Template System__: Pre-built workflow patterns
- __Visual Chain Builder__: Interactive workflow construction

## 3. Enhanced Mode System

**Target Location:** `app/modes/`, `config/modes/`

- __Context Modes__: Research, Creative, Technical, Debug with optimized prompts
- __Mode Inheritance__: Hierarchical mode configuration
- __Dynamic Mode Switching__: Context-aware mode transitions
- __Custom Mode Creation__: User-defined modes with specialized behaviors

## 4. Plugin Architecture

**Target Location:** `plugins/`, `app/plugin_manager.py`

- __Provider Plugins__: Easy addition of new LLM providers
- __Filter Plugins__: Content processing and transformation
- __Output Plugins__: Custom response formatting and export
- __Integration Plugins__: External tool connections



# Roadmap

## High-Level Vision

The llm-orchestrator aims to be a powerful, local-first, and highly extensible tool for developers and researchers to manage complex interactions with Large Language Models. Our vision is to create a system that is not only robust and secure but also transparent and easy to understand, fostering a collaborative and innovative environment.

For more detailed, actionable items, please see the GitHub Issues for this project. For major architectural decisions, please refer to the Architecture Decision Records (ADRs) in the `docs/architecture/adr` directory. For a more technical breakdown of the ideas listed below, see the [Future Development Ideas](docs/future-development.md) document.

## Future Directions

### Evolving the Orchestration Paradigm
We plan to explore more sophisticated orchestration paradigms beyond simple parallel and sequential queries, such as conversation-driven, process-centric, and toolkit-based orchestration.

### Enhancing Tool Usage and Extensibility
We will investigate integrating with standardized tool management systems like the Model Context Protocol (MCP) to expand the orchestrator's capabilities and allow for more seamless integration of external tools.

### Strengthening Security and Trust Mechanisms
We will enhance the security of the orchestrator by incorporating principles such as user consent and control for all operations, mandatory human approval for tool invocations, and a robust authorization framework.

### Advanced State and Memory Management
We will explore more dynamic memory systems, such as vector databases and tiered memory systems, to enable more complex operations and long-term memory.

### Enhancing Internal Code Representation and Understanding
We will improve the clarity and maintainability of the codebase by enforcing comprehensive docstrings, using hyperlinks to connect code to documentation, and exploring AI-powered code summarization and interactive code-knowledge graphs.

### Robust Prompt Management and Optimization
We will implement more robust prompt management and optimization techniques, including advanced templating, versioning, and A/B testing, to improve the performance and reliability of the orchestrator.



---

### project-structure.md
# Project Structure

This document outlines the directory structure of the `llm-orchestrator` project.

```
/
├── app/                # Core application logic
│   ├── __init__.py
│   ├── chat.py         # Interactive chat functionality
│   ├── clients.py      # Clients for different LLM providers
│   ├── key_management.py # Secure vault and key handling
│   ├── main.py         # Main CLI entry point (using Click)
│   ├── orchestrator.py # Logic for running queries
│   └── session.py      # Manages user session and configuration
├── conversations/      # Stores conversation history (auto-generated)
├── docs/               # Project documentation
│   ├── architecture/   # C4 model diagrams and ADRs
│   ├── usage/          # User guides (installation, configuration)
│   └── contributing.md # Guidelines for contributors
├── scripts/            # Helper scripts for development and setup
├── tests/              # Unit and integration tests
├── .gitignore          # Files and directories ignored by Git
├── config.yaml         # Main configuration file
├── models.yaml         # Configuration for LLM models
├── poetry.lock         # Poetry lock file for dependency management
├── pyproject.toml      # Project metadata and dependencies for Poetry
├── README.md           # Main project README
└── ROADMAP.md          # High-level project roadmap
```


---

### cli-reference.md
# CLI Reference

This page provides a reference for the command-line interface of the llm-orchestrator.

## Global Options

*   `--help`: Show the help message and exit.

## Commands

### `chat`

Start an interactive chat session.

### `run`

Run a single query.

#### Options

*   `--prompt`: The prompt to send to the LLM.
*   `--model`: The model to use for the query.
*   `--parallel`: Run queries in parallel.
*   `--sequential`: Run queries sequentially.


---

### configuration.md
# Configuration

The LLM Orchestrator CLI is configured through two YAML files: `config.yaml` and `models.yaml`.

## `config.yaml`

This file stores the main configuration for the application.

-   `main_llm`: This section defines the default provider and model to be used when the application starts.
-   `chains`: This section stores any saved chains that you have created.

Here is an example `config.yaml` file:

```yaml
main_llm:
  provider: gemini
  model: gemini-1.5-flash-latest
chains:
  my_chain:
    - "GenerateCode>/Developer)-gemini"
    - "Critique>/Tester)-anthropic"
```

## `models.yaml`

This file stores the configuration for the different providers and models that the application can use.

-   **Provider**: Each top-level key in this file is a provider (e.g., `gemini`, `anthropic`).
-   `api_key_name`: This is the name of the API key that the application will look for in the vault.
-   `default_model`: This is the default model that will be used for this provider if no other model is specified.
-   `models`: This is a list of the models that are available for this provider. Each model can have its own specific parameters (e.g., `max_tokens`, `temperature`).

Here is an example `models.yaml` file:

```yaml
anthropic:
  api_key_name: ANTHROPIC_API_KEY
  default_model: claude-3-5-sonnet-20240620
  models:
    - name: claude-3-5-sonnet-20240620
      max_tokens: 4096
    - name: claude-3-haiku-20240307
      max_tokens: 1000

gemini:
  api_key_name: GEMINI_API_KEY
  default_model: gemini-1.5-flash-latest
  models:
    - name: gemini-1.5-flash-latest
      temperature: 0.7
    - name: gemini-1.5-pro-latest
      temperature: 0.7
```


---

### installation.md
# Installation

This project is managed with [Poetry](https://python-poetry.org/), which handles dependency management and virtual environments automatically.

## 1. Install Poetry

First, if you don't have Poetry, install it by following the [official instructions](https://python-poetry.org/docs/#installation).

## 2. Clone the Repository

Clone the project repository from GitHub:

```bash
git clone https://github.com/your-username/llm_orchestrator.git
cd llm_orchestrator
```

## 3. Install Dependencies

Poetry will read the `pyproject.toml` file, create a virtual environment, and install all necessary dependencies with a single command:

```bash
poetry install
```

## 4. Set Up the API Key Vault

Your LLM API keys are stored securely in an encrypted vault. To initialize the vault and add your keys, run the settings manager:

```bash
poetry run python settings.py
```

Select **[1] Initialize a new vault** and follow the prompts.

## 5. (Optional) Install Shell Completion

For a much better user experience, install the shell completion script. This will enable tab-completion for commands, options, and even chain names.

Run the following command for your shell (using `poetry run`):

=== "Bash"
    ```bash
    poetry run python -m app.main install-completion --shell bash
    ```
    Then add this to your `~/.bashrc`:
    ```bash
    eval "$(_LLM_ORCHESTRATOR_CLI_COMPLETE=bash_source llm-orchestrator-cli)"
    ```

=== "Zsh"
    ```bash
    poetry run python -m app.main install-completion --shell zsh
    ```
    Then add this to your `~/.zshrc`:
    ```bash
    eval "$(_LLM_ORCHESTRATOR_CLI_COMPLETE=zsh_source llm-orchestrator-cli)"
    ```

=== "Fish"
    ```bash
    poetry run python -m app.main install-completion --shell fish
    ```
    Then add this to your `~/.config/fish/config.fish`:
    ```bash
    eval (env _LLM_ORCHESTRATOR_CLI_COMPLETE=fish_source llm-orchestrator-cli)
    ```

After updating your shell's configuration file, restart your shell for the changes to take effect.


Now you are ready to use the LLM Orchestrator CLI! Try running `poetry run python -m app.main --help` to see the available commands.
