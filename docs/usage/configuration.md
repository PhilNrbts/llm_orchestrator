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
