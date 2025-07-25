# C2: High-Level Components Diagram

This diagram shows the major high-level components within the llm-orchestrator system.

*(Note: In the C4 model, these are called "Containers," but we are using the term "High-Level Components" to avoid confusion with Docker containers.)*

![Component Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## High-Level Components

*   **CLI App:** The main command-line interface application that users interact with.
*   **Vault:** The secure, encrypted file that stores API keys and other sensitive data.
*   **Config Files:** The YAML files that store the application's configuration.
*   **Orchestration Engine:** The core component that manages interactions with LLMs.
*   **LLM Clients:** The individual clients for each supported LLM provider.
