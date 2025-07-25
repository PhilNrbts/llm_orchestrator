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
