# Commands

The CLI is organized into several command groups. You can always get more information about a command by using the `--help` flag.

## Interactive Chat

The primary way to use the application is through the interactive chat. To start the chat, simply run the application without any commands:

```bash
llm-orchestrator
```

### Slash Commands

The interactive chat has a number of slash commands to control the application:

-   `/help`: Show a list of available commands.
-   `/changemodel`: Change the model used in the chat.
-   `/changeprovider`: Change the provider used in the chat.
-   `/list`: List the available models for the current provider.
-   `/config`: Show the current configuration.
-   `/mode`: Change the chat mode.
-   `/exit` or `/quit`: Exit the chat.

## `run`

The `run` command is a secondary way to execute queries.

### Parallel Queries

To send a prompt to multiple models at once, use the `--model` flag:

```bash
llm-orchestrator run -p "What is the future of AI?" --model gemini --model anthropic
```

### Sequential Chains (On-the-Fly)

To create a chain of queries, use the `--step` flag. The format is `Role>/Persona)-Model`.

```bash
llm-orchestrator run -p "Write a python function for fibonacci" \
    --step "GenerateCode>/Developer)-gemini" \
    --step "Critique>/Tester)-anthropic"
```

## `chain`

The `chain` command group lets you manage saved workflows.

-   `llm-orchestrator chain list`: Lists all chains saved in `config.yaml`.
-   `llm-orchestrator chain run <chain_name> -p "Your prompt"`: Executes a saved chain.
-   `llm-orchestrator chain save <chain_name> --step "..."`: Saves a new chain.

## `auth`

The `auth` command group manages password sessions.

-   `llm-orchestrator auth start`: Starts a 15-minute session where you don't need to re-enter your password.
-   `llm-orchestrator auth stop`: Ends the current session.
