# Understanding Chains

Chains are the most powerful feature of the LLM Orchestrator. They allow you to create sophisticated workflows where the output of one model becomes the input for the next.

## On-the-Fly Chains

You can create a temporary chain directly from the command line using the `--step` flag with the `run` command. This is useful for experiments and one-off tasks.

The syntax for a step is:

```
"Role>/Persona)-Model"
```

-   **Role**: The action the model should take (e.g., `Critique`, `Summarize`, `GenerateCode`).
-   **Persona**: The "personality" the model should adopt (e.g., `Developer`, `Poet`, `Tester`).
-   **Model**: The LLM to use for this step (e.g., `gemini`, `anthropic`).

### Example

This example first generates code with Gemini and then asks Anthropic to critique it.

```bash
my-cli run -p "Write a python function for fibonacci" \
    --step "GenerateCode>/Developer)-gemini" \
    --step "Critique>/Tester)-anthropic"
```

## Saved Chains

For workflows you use frequently, you can save them as a named chain in your `config.yaml` file.

### Saving a Chain

Use the `chain save` command:

```bash
my-cli chain save my_analysis_workflow \
    --step "Summarize>/TechnicalWriter)-gemini" \
    --step "Plan>/ProductManager)-anthropic"
```

This saves a chain named `my_analysis_workflow` to your `config.yaml`.

### Running a Saved Chain

Use the `chain run` command:

```bash
my-cli chain run my_analysis_workflow -p "The latest report on AI trends"
```

This will execute the two steps defined in the `my_analysis_workflow` chain.

```