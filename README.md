# LLM Orchestrator CLI

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

For full installation and usage instructions, please see the [complete documentation](https://baggy.github.io/llm_orchestrator/).

To build and serve the documentation locally, run:

```bash
poetry run mkdocs serve
```
