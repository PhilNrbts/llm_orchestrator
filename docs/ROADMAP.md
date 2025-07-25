# Roadmap

The llm-orchestrator aims to be a powerful, local-first, and highly extensible tool for developers and researchers to manage complex interactions with Large Language Models.

---

## Development Roadmap

This section contains a breakdown of potential future features and improvements.

### 1. Workflow Definition and Parameterization
To enable powerful and modular orchestrations, we will implement a declarative workflow definition system. Users will define reusable workflows (or "chains") in `config.yaml` as a list of steps. Each step defines a task, its required inputs, and its execution context.

**Core Concepts**
- **Parameters (params):** Each workflow can define input parameters.
- **Input Validation Schema:** To prevent runtime failures, parameters will support basic type validation. This makes workflows self-documenting and resilient to malformed inputs.
- **Steps (steps):** A workflow consists of one or more steps that invoke registered tools.
- **Inputs (inputs):** Tool arguments are populated dynamically from parameters or the outputs of previous steps using a simple `{{...}}` syntax.
- **Scrutiny Gates (gate):** A step can be marked as a gate, pausing the workflow to await user approval. This is crucial for review, validation, and adding a human-in-the-loop.

**Implement a Configuration Validation Schema:**
- **Action:** Create a set of Pydantic models that define the valid structure for `config.yaml`.
- **Rule:** The application must parse the configuration through these models on startup, providing clear, actionable error messages to the user if validation fails. This ensures that all user-defined workflows are structurally sound before execution.

**Example: Research Workflow with a Scrutiny Gate**
This example shows how a gate can be added to allow the user to review a critique before the final draft is written.
```yaml
# In config.yaml

workflows:
  detailed_research:
    params:
      - query
      - draft_model: "gemini-1.5-pro"
      - critique_model: "claude-3-opus"

    steps:
      - name: "generate_draft"
        tool: "model_call"
        inputs:
          # ... (inputs for draft generation)

      - name: "get_critique"
        tool: "model_call"
        inputs:
          # ... (inputs for critique generation)

      # --- GATE IMPLEMENTATION ---
      - name: "review_critique"
        gate: # This key marks the step as a scrutiny gate
          prompt: |
            The following critique has been generated.
            Review it and decide whether to proceed with the final refinement.
            ---
            Critique: {{steps.get_critique.output}}
            ---
            Approve (y/n)?

      - name: "final_refinement"
        tool: "model_call"
        # This step will only run if the "review_critique" gate is approved
        inputs:
          model: "{{params.draft_model}}"
          prompt: |
            You have received the following critique of your initial draft.
            Critique: {{steps.get_critique.output}}
            ---
            Original Draft: {{steps.generate_draft.output}}
            ---
            Please rewrite the draft, fully addressing all points in the critique.
```
By adding Scrutiny Gates to your workflow ambitions, you create a system that is not only powerful and automated but also transparent, controllable, and trustworthy.

### 2. Enhanced Tool Usage and Extensibility
- **Standardized Tool Integration (MCP):** Function as a Model Context Protocol (MCP) client to access a growing list of pre-built integrations for file operations, database access, and web search.
- **Composability:** Design for highly composable servers and capabilities to support greater extensibility.

### 3. Strengthened Security and Trust
- **User Consent and Control:** Provide clear UI for user review and authorization for all operations.
- **Human-in-the-Loop:** Implement mandatory human approval for tool invocations, especially for destructive operations.
- **Authorization Framework:** Implement an OAuth 2.1-based authorization framework for secure interactions.

### 4. ✅ Advanced Memory Management: Fractured Context - **COMPLETED!**
**Status:** ✅ **IMPLEMENTED** (January 2025)
**Documentation:** [`docs/cline/phase4-advanced-memory-management.md`](cline/phase4-advanced-memory-management.md)

The fractured memory system has been fully implemented! This moves beyond simple all-or-nothing context history and allows each workflow step to precisely define the "slice" of conversation context it needs. This prevents context bloat and ensures workflows operate predictably with intelligent context awareness.

**✅ Implemented Features:**
- **SQLite-based Memory Store:** Local-first database storing memory slices with rich metadata
- **Memory Manager:** Intelligent context orchestration and template variable injection
- **Context Slicing:** Steps specify exactly what context they receive via `memory.needs` configuration
- **Template Variables:** Support for `{{memory.variable}}` syntax in prompts
- **Workflow Integration:** Seamless integration with existing workflow engine
- **Comprehensive Testing:** Full test suite with real API integration verified

**✅ Working Configuration Example:**
```yaml
workflows:
  sequential_elaboration:
    steps:
      - name: initial_answer
        tool: "model_call"
        inputs:
          prompt: "{{params.user_prompt}}"

      - name: elaboration_generator
        memory:
          needs: ["user_prompt", "tool_output(initial_answer)"]
        inputs:
          prompt: "Given '{{memory.user_prompt}}' and '{{memory.initial_answer_output}}', elaborate..."

      - name: responder
        memory:
          needs: ["tool_output(elaboration_generator)"]
        inputs:
          prompt: "{{memory.elaboration_generator_output}}"
```

**✅ Memory Patterns Supported:**
- `user_prompt` - Original user input
- `tool_output(step_name)` - Output from specific step
- `last_output` - Most recent step output
- `parameters` - Workflow parameters
- Custom classifications and metadata

**✅ Key Benefits Achieved:**
- **Persistent Context:** Workflows maintain state across steps
- **Intelligent Prompting:** Dynamic prompt generation using memory context
- **Complex Reasoning:** Multi-step workflows with full context awareness
- **Production Ready:** SQLite database with comprehensive error handling and testing

The memory system now enables sophisticated multi-step AI orchestration workflows where each step intelligently builds upon previous results. This represents a major architectural advancement from stateless command processing to context-aware intelligent workflows.

### 5. Developer Experience and Maintainability
To ensure the project remains healthy and easy to contribute to, we will implement the following concrete actions. This replaces abstract goals with tangible development practices.

**Establish a Clear ADR Process:**
- **Action:** Create a formal template for Architecture Decision Records (ADRs) in the `docs/architecture/adr` directory.
- **Rule:** Any significant change to the core architecture (e.g., adding a new memory system, changing the plugin API) must be preceded by an accepted ADR. This provides a clear, documented history of why decisions were made.

**Implement Code Quality Gates:**
- **Action:** Configure pre-commit hooks to run on every commit.
- **Checks:**
  - **Formatting:** Automatically format code with `black`.
  - **Linting:** Enforce code quality standards with `ruff`.
  - **Docstring Coverage:** Initially, check that all new functions have docstrings; later, enforce a minimum coverage percentage.

### 6. Robust Prompt Management
- **Interactive Prompt Reformulation:** Add a flag (`--reformulate`) to allow a smaller, faster model to reformulate the user's initial prompt. The reformulated prompt will be presented to the user for confirmation or revision before being sent to the primary model.
  - **Settings (`config.yaml`):**
    - `reformulation.model`: Specify the default provider and model (e.g., `provider: gemini`, `model: gemini-1.5-flash`).
    - `reformulation.prompt`: Store the default reformulation instruction (e.g., "Reformulate the following to be clearer...").
    - `reformulation.custom_prompt_path`: Allow users to specify a path to a file containing a custom prompt, which overrides the default.
- **Advanced Templating:** Use engines like Jinja2 for complex prompt logic.
- **Versioning and Management:** Implement robust prompt versioning using Git-based systems or specialized platforms.
- **Optimization and Tuning:** Employ both manual A/B testing and automated prompt generation/refinement.
- **Evaluation Metrics:** Establish clear metrics (human, model-based, or quantitative) to objectively assess prompt performance.
