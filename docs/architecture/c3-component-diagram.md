# C3: Component Diagram

This diagram shows the components within the CLI App container.

![Component Diagram](https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjDBSvQS02000)

## Components

*   **Main (main.py):** The entry point for the CLI application. It uses `click` to define the commands and options.
*   **Orchestrator (orchestrator.py):** This component is responsible for managing the overall workflow. It takes a user's query, determines which LLMs to use, and whether to run them in parallel or sequentially.
*   **LLM Clients (clients.py):** This module contains the individual clients for each LLM provider (e.g., OpenAI, Anthropic). Each client is responsible for making the actual API calls to the provider.
*   **Key Management (key_management.py):** This component interacts with the secure vault to retrieve and manage API keys.
*   **Session (session.py):** This component manages the user's session, including loading configuration and handling conversation history.
*   **Chat (chat.py):** This component provides the interactive chat functionality.
