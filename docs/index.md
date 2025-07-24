# Welcome to the LLM Orchestrator CLI

The LLM Orchestrator is a powerful, local-first command-line tool designed for developers, researchers, and writers who need to interact with multiple Large Language Models (LLMs) efficiently. It provides a secure and flexible way to run queries and manage workflows directly from your terminal.

## Key Features

- **Interactive Chat**: The primary way to use the application. A rich terminal UI with a command dropdown, chat history, and model details.
- **Secure API Key Management**: Your API keys are encrypted locally in a `vault.enc` file. A master password decrypts them in memory only when needed.
- **Parallel Queries**: Send a single prompt to multiple models (like Gemini, Anthropic, etc.) at the same time and compare their responses side-by-side.
- **On-the-Fly Chains**: Construct powerful, sequential workflows directly on the command line. Use the output of one model as the input for the next, with custom roles and personas for each step.
- **Saved Chains**: Save your most-used workflows to a `config.yaml` file for easy reuse.
- **Session Management**: Start an authenticated session to avoid entering your password for every command.

## Getting Started

Ready to dive in? Head over to the [**Installation**](usage/installation.md) guide to get started.