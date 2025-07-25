# C1: System Context

This diagram shows the system context for the llm-orchestrator.

![System Context Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## Users

*   **Developer:** A software developer who uses the llm-orchestrator to interact with various LLMs.

## System

*   **llm-orchestrator:** The command-line tool that provides the core functionality.

## External Dependencies

*   **LLM Providers:** External services like OpenAI, Anthropic, etc., that provide the language models.
*   **Configuration Files:** Local files that store settings and API keys.
*   **Secure Vault:** An encrypted local file for storing sensitive data.
