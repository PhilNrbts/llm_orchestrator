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
