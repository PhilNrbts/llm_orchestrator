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
