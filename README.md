# Containerized Multi-LLM Orchestrator

This project provides a secure, containerized, and cross-platform framework to interact with multiple Large Language Models (LLMs) like Anthropic, Gemini, DeepSeek, and Mistral. It can run in two modes:
1.  **Parallel Mode**: Sends the same prompt to all models simultaneously and returns a collection of responses.
2.  **Sequential Refinement Mode**: Chains the models in a specified order, where each model refines the output of the previous one.

The entire application runs within a Docker container, accessible via a FastAPI web server, ensuring consistency across different environments like Windows (via WSL2) and Android (via Termux).

---

## Features

-   **Secure API Key Storage**: Uses PBKDF2 for key derivation and Fernet (AES-128-CBC) for encrypting API keys in a `vault.enc` file. The password is never stored.
-   **Dual Execution Modes**: Flexible parallel or sequential processing of prompts.
-   **Containerized with Docker**: Easy to set up and run consistently on any system with Docker support.
-   **Host Filesystem Access**: The container can be configured to read from and write to a directory on the host machine, similar to the Gemini CLI's file access.
-   **Cross-Platform**: Includes setup scripts for both Windows (PowerShell) and Android (Termux/Bash).
-   **Web API**: Exposes a simple REST API using FastAPI for easy integration.

---

## Project Structure

llm_orchestrator/
├── app/
│   ├── init.py
│   ├── orchestrator.py      # FastAPI application core
│   ├── clients.py           # LLM client implementations
│   └── init_vault.py        # Script to create the encrypted API key vault
├── scripts/
│   ├── setup_windows.ps1    # Setup script for Windows/WSL2
│   └── setup_android.sh     # Setup script for Android/Termux
├── workspace/               # Mount point for host filesystem (created empty)
├── .gitignore
├── Dockerfile
├── models.yaml              # Configuration for different models
├── README.md
└── requirements.txt         # Python dependencies


---

## Setup and Deployment

### Quick Start (One-Liner)

For the fastest setup on Linux, macOS, or WSL, you can run the following command in your terminal. It will download and run the interactive setup script without needing to clone the repository first.

```bash
bash <(curl -s https://raw.githubusercontent.com/PhilNrbts/llm_orchestrator/master/setup_interactive.sh)
```

After the script completes, you can run the service as instructed.

### Other Setup Options

For the best experience, we recommend using the provided interactive setup script or the VS Code Dev Container.

#### Recommended: Interactive Setup

An interactive script is provided to guide you through the setup process. To use it, make it executable and run it:
```bash
chmod +x setup_interactive.sh
./setup_interactive.sh
```
Alternatively, you can use the `setup.ipynb` Jupyter Notebook for a cell-by-cell guided setup.

#### Development Environment: VS Code Dev Containers

This project is configured to use VS Code Dev Containers, which provides a fully-featured development environment running inside Docker. This is the recommended way to develop and contribute to this project.

1.  Make sure you have the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) installed in VS Code.
2.  Open the project folder in VS Code.
3.  Click the "Reopen in Container" button when prompted.

This will build the container and connect your VS Code instance to it, providing a seamless development experience.

#### Manual Setup

If you prefer a manual setup, follow these steps:

##### Step 1: Build the Docker Image
```bash
docker build -t llm-orchestrator .
```

##### Step 2: Initialize the Encrypted Vault
Run the vault script to securely store your API keys. You will be prompted for your keys and a master password.
```bash
docker run -it --rm --entrypoint python -v "${PWD}:/app" llm-orchestrator app/init_vault.py
```

##### Step 3: Run the Orchestrator Service
Run the container in detached mode, mapping the necessary ports and volumes.
-   **On Linux/macOS/WSL:**
    ```bash
    docker run -d --name llm-engine -p 8000:8000 -v "${PWD}/vault.enc:/vault.enc" -v "${PWD}/models.yaml:/models.yaml" -v "${PWD}/workspace:/workspace" --rm llm-orchestrator
    ```
-   **On Android (from Termux after proot-distro login):**
    ```bash
    docker run -d --name llm-engine -p 8000:8000 -v "$HOME/storage/shared/LLMWorkspace:/workspace" -v "$(pwd)/vault.enc:/vault.enc" -v "$(pwd)/models.yaml:/models.yaml" --rm llm-orchestrator
    ```
    *Note: Make sure the `LLMWorkspace` directory exists in your Android's shared storage.*

---

## Usage

Interact with the service using any HTTP client, like `curl`.

### Example: Parallel Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "password": "your-secret-password",
    "mode": "parallel"
  }'
Example: Sequential Refinement Query
Bash

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How can we reduce AI bias in healthcare diagnostics?",
    "password": "your-secret-password",
    "mode": "sequential"
  }'
Execution Workflow
Code snippet

graph TD
    A[User] -->|Request via curl| B(FastAPI Endpoint)
    B -->|Password| C{Decrypt Vault}
    C -->|API Keys| D{Execution Mode?}
    D -->|Parallel| E[Asyncio Gather: Run all models]
    D -->|Sequential| F[For Loop: Chain model outputs]
    E --> G[Combine JSON responses]
    F --> H[Generate refinement chain]
    G & H --> I[Return Final JSON to User]
    subgraph Container
        B
        C
        D
        E
        F
        G
        H
        I
    end
    subgraph "Host Machine"
        J(Host Files)
        K(Internet)
    end
    I -- Access --> J
    I -- Access --> K

```