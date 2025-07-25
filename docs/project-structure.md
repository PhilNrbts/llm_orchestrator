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
