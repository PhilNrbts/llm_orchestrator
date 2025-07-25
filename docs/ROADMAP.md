# Roadmap

The llm-orchestrator aims to be a powerful, local-first, and highly extensible tool for developers and researchers to manage complex interactions with Large Language Models.

---

## Development Roadmap

This section contains a breakdown of potential future features and improvements.

### 1. Evolving the Orchestration Paradigm
- **Advanced Parallel Processing with Summarization:** After an optional prompt reformulation, run a query against multiple models in parallel. In a second step, use a dedicated model to summarize the collected responses.
  - **Settings (`config.yaml`):**
    - `parallel_processing.summarizer.model`: Specify the provider and model for the summarization step (defaults to the main app model).
    - `parallel_processing.summarizer.prompt`: Define the default prompt for the summarizer.
    - `parallel_processing.ui.show_summary`: A boolean flag to control whether the final summary is displayed in the output.
- **Conversation-Driven Orchestration (e.g., AutoGen):** Support dynamic routing of tasks based on conversational flow.
- **Process-Centric & Role-Based Orchestration (e.g., CrewAI):** Simplify task delegation with structured workflows and roles.
- **Toolkit-Based Orchestration (e.g., LangChain Agents):** Offer modularity and a vast ecosystem of tools.
- **SOP-Driven Orchestration (e.g., MetaGPT):** Ensure coherent outputs for complex tasks using standardized processes.
- **Configurable Sequential Chains:** Allow users to define multi-step workflows where the output of one model becomes the input for the next.
  - **User-Defined Goals:** For each step in the chain, the user will define the `model` to use and a `prompt_template` that sets the goal for that step (e.g., "Critique this code: `{{previous_response}}`").
  - **Self-Correction Pattern:** This allows for chains where a model refines its own output by using the same model for multiple, goal-oriented steps.
- **Integrate Reflection Capabilities (e.g., Devon/Reflexion):** Allow the orchestrator to reflect on past decisions to improve future performance and aid in prompt optimization.

### 2. Enhanced Tool Usage and Extensibility
- **Standardized Tool Integration (MCP):** Function as a Model Context Protocol (MCP) client to access a growing list of pre-built integrations for file operations, database access, and web search.
- **Composability:** Design for highly composable servers and capabilities to support greater extensibility.

### 3. Strengthened Security and Trust
- **User Consent and Control:** Provide clear UI for user review and authorization for all operations.
- **Human-in-the-Loop:** Implement mandatory human approval for tool invocations, especially for destructive operations.
- **Authorization Framework:** Implement an OAuth 2.1-based authorization framework for secure interactions.

### 4. Advanced State and Memory Management
- **Vector Databases:** Utilize vector databases (e.g., Pinecone, Weaviate) for shared knowledge and long-term memory.
- **Tiered Memory Systems (e.g., MemGPT):** Implement a tiered memory system to manage long-context retention.
- **Generative Agents Memory Stream:** Incorporate a memory architecture that records and retrieves past experiences for reflection and planning.

### 5. Enhanced Internal Code Representation
- **Comprehensive Docstrings:** Ensure all code units have detailed docstrings.
- **Hyperlinking:** Systematically use hyperlinks within code and documentation to connect related artifacts (ADRs, issues, etc.).
- **AI-Powered Code Summarization:** Automatically generate summaries of code blocks to aid understanding.
- **Interactive Code-Knowledge Graphs:** Represent the codebase as a structured knowledge graph to provide a holistic view of the architecture and dependencies.

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
