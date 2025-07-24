gemini "Please create a project folder named 'llm_orchestrator' and populate it with the following files and content. This project sets up a containerized, multi-LLM orchestration service.

**1. README.md:** Create a comprehensive readme file that explains the project.
`llm_orchestrator/README.md`
```markdown
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

### Prerequisites
-   **Windows**: WSL2 and Docker Desktop installed.
-   **Android**: Termux and `proot-distro` for running a Linux distribution with Docker support.

### Step 1: Initialize the Encrypted Vault

First, you need to securely store your API keys.

1.  **Build the Docker image:**
    ```bash
    docker build -t llm-orchestrator .
    ```

2.  **Run the vault initialization script:**
    ```bash
    docker run -it --rm -v "${PWD}:/app" llm-orchestrator python app/init_vault.py
    ```
    You will be prompted to enter your API keys and set a master password for the vault. This will create a `vault.enc` file in your project directory.

### Step 2: Run the Orchestrator Service

Run the container in detached mode, mapping the port and the workspace volume.

-   **On Windows (from PowerShell/WSL):**
    ```bash
    docker run -d --name llm-engine -p 8000:8000 -v "${PWD}/workspace:/workspace" -v "${PWD}/vault.enc:/app/vault.enc" --rm llm-orchestrator
    ```
-   **On Android (from Termux after proot-distro login):**
    ```bash
    docker run -d --name llm-engine -p 8000:8000 -v "$HOME/storage/shared/LLMWorkspace:/workspace" -v "$(pwd)/vault.enc:/app/vault.enc" --rm llm-orchestrator
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

**2. Dockerfile:** Create the Dockerfile for the container.
`llm_orchestrator/Dockerfile`
```dockerfile
# Use a slim Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies that some libraries might need
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY ./app /app/

# Mount point for host filesystem access
VOLUME /workspace

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application
ENTRYPOINT ["uvicorn", "app.orchestrator:app", "--host", "0.0.0.0", "--port", "8000"]
3. requirements.txt: Create the Python dependencies file.
llm_orchestrator/requirements.txt

fastapi
uvicorn[standard]
pydantic
python-multipart
cryptography
anthropic
google-generativeai
deepseek-api
mistralai
4. .gitignore: Create a standard gitignore file.
llm_orchestrator/.gitignore

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Security
vault.enc
.env.enc
.key.enc
vault.lock
*.pem
*.key

# IDE specific files
.idea/
.vscode/
5. models.yaml: Create the model configuration file.
llm_orchestrator/models.yaml

YAML

anthropic:
  model: "claude-3-haiku-20240307"
  max_tokens: 1000
gemini:
  model: "gemini-1.5-flash"
  temperature: 0.7
deepseek:
  model: "deepseek-chat"
  max_tokens: 1024
mistral:
  model: "mistral-large-latest"
  temperature: 0.5
6. Application Source Code:

llm_orchestrator/app/__init__.py

Python

# This file can be left empty.
llm_orchestrator/app/init_vault.py

Python

import getpass
import os
import hashlib
import base64
from cryptography.fernet import Fernet

VAULT_FILE = "vault.enc"
# In a real production system, this salt should be managed securely
# and not hardcoded. For this project, it's set here for simplicity.
PASSWORD_SALT = b"a-secure-random-salt-should-be-used-here"

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a stable encryption key from a password."""
    kdf = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000,  # Recommended iterations
        32
    )
    return base64.urlsafe_b64encode(kdf)

def main():
    """Main function to create and encrypt the API key vault."""
    print("--- Secure API Key Vault Setup ---")
    if os.path.exists(VAULT_FILE):
        overwrite = input(f"Warning: '{VAULT_FILE}' already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Vault setup cancelled.")
            return

    keys = {
        "ANTHROPIC_API_KEY": getpass.getpass("Enter Anthropic API Key: "),
        "GEMINI_API_KEY": getpass.getpass("Enter Gemini API Key: "),
        "DEEPSEEK_API_KEY": getpass.getpass("Enter DeepSeek API Key: "),
        "MISTRAL_API_KEY": getpass.getpass("Enter Mistral API Key: ")
    }

    password = getpass.getpass("Set a master password for the vault: ")
    confirm_password = getpass.getpass("Confirm master password: ")

    if password != confirm_password:
        print("\nError: Passwords do not match. Aborting.")
        exit(1)
    
    if not password:
        print("\nError: Password cannot be empty. Aborting.")
        exit(1)

    # Prepare data for encryption
    env_content = "\n".join(f"{key}={value}" for key, value in keys.items())

    # Encrypt and store
    try:
        encryption_key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(encryption_key)
        encrypted_data = cipher.encrypt(env_content.encode('utf-8'))

        with open(VAULT_FILE, "wb") as f:
            f.write(encrypted_data)
        
        print(f"\nSuccess! API keys encrypted and saved to '{VAULT_FILE}'.")
        print("Keep your master password safe. It is not recoverable.")

    except Exception as e:
        print(f"\nAn unexpected error occurred during encryption: {e}")

if __name__ == "__main__":
    main()
llm_orchestrator/app/clients.py

Python

import asyncio

# --- Placeholder Client Implementations ---
# In a real application, you would replace these with actual API calls
# using the respective client libraries (e.g., anthropic, google.generativeai)

class BaseClient:
    def __init__(self, api_key: str, model_name: str = "default"):
        self.api_key = api_key
        self.model_name = model_name

    async def query(self, prompt: str):
        raise NotImplementedError("Query method must be implemented by subclasses.")

class AnthropicClient(BaseClient):
    async def query(self, prompt: str):
        # Placeholder: Replace with actual anthropic.Anthropic().messages.create(...) call
        print(f"Querying Anthropic ({self.model_name})...")
        await asyncio.sleep(0.5) # Simulate network latency
        return f"Anthropic response for: '{prompt[:30]}...'"

class GeminiClient(BaseClient):
    async def query(self, prompt: str):
        # Placeholder: Replace with actual generative_models.GenerativeModel().generate_content(...) call
        print(f"Querying Gemini ({self.model_name})...")
        await asyncio.sleep(0.4) # Simulate network latency
        return f"Gemini response for: '{prompt[:30]}...'"

class DeepSeekClient(BaseClient):
    async def query(self, prompt: str):
        # Placeholder: Replace with actual deepseek API call
        print(f"Querying DeepSeek ({self.model_name})...")
        await asyncio.sleep(0.6) # Simulate network latency
        return f"DeepSeek response for: '{prompt[:30]}...'"

class MistralClient(BaseClient):
    async def query(self, prompt: str):
        # Placeholder: Replace with actual mistral_client.Client().chat(...) call
        print(f"Querying Mistral ({self.model_name})...")
        await asyncio.sleep(0.5) # Simulate network latency
        return f"Mistral response for: '{prompt[:30]}...'"

def get_client(client_name: str, api_key: str, model_name: str = "default"):
    """Factory function to get a client instance."""
    client_map = {
        "anthropic": AnthropicClient,
        "gemini": GeminiClient,
        "deepseek": DeepSeekClient,
        "mistral": MistralClient,
    }
    client_class = client_map.get(client_name.lower())
    if not client_class:
        raise ValueError(f"Unknown client: {client_name}")
    return client_class(api_key=api_key, model_name=model_name)
llm_orchestrator/app/orchestrator.py

Python

import os
import asyncio
import hashlib
import base64
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet, InvalidToken

from app.clients import get_client

# --- Configuration ---
VAULT_FILE_PATH = os.environ.get("VAULT_FILE_PATH", "/app/vault.enc")
PASSWORD_SALT = b"a-secure-random-salt-should-be-used-here"
MODEL_SEQUENCE = ["gemini", "anthropic", "mistral", "deepseek"]

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Multi-LLM Orchestrator",
    description="An API to query multiple LLMs in parallel or sequentially.",
    version="1.0.0",
)

# --- Security and Key Management ---
def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a stable encryption key from a password."""
    kdf = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), salt, 100000, 32
    )
    return base64.urlsafe_b64encode(kdf)

def get_api_keys(password: str) -> Dict[str, str]:
    """Decrypt the vault and return API keys."""
    if not os.path.exists(VAULT_FILE_PATH):
        raise HTTPException(status_code=500, detail=f"Vault file not found at {VAULT_FILE_PATH}. Please run init_vault.py.")
    try:
        with open(VAULT_FILE_PATH, "rb") as f:
            encrypted_data = f.read()
        
        encryption_key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(encryption_key)
        decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
        
        keys = dict(line.split("=", 1) for line in decrypted_data.splitlines() if line)
        return keys
    except InvalidToken:
        raise HTTPException(status_code=403, detail="Invalid password or corrupted vault.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to decrypt vault: {e}")

# --- API Models ---
class QueryRequest(BaseModel):
    prompt: str
    password: str = Field(..., description="The master password for the API key vault.")
    mode: str = Field("parallel", enum=["parallel", "sequential"], description="Execution mode.")

class ParallelResponse(BaseModel):
    results: Dict[str, str]

class SequentialResponse(BaseModel):
    conversation: List[Dict[str, str]]

# --- Core Orchestration Logic ---
async def parallel_query(prompt: str, api_keys: Dict[str, str]) -> Dict[str, str]:
    """Query all models simultaneously."""
    tasks = []
    model_names = list(api_keys.keys())

    for key_name in model_names:
        model_id = key_name.replace("_API_KEY", "").lower()
        client = get_client(model_id, api_keys[key_name])
        tasks.append(client.query(prompt))

    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = {}
    for i, model_key in enumerate(model_names):
        model_id = model_key.replace("_API_KEY", "").lower()
        if isinstance(responses[i], Exception):
            results[model_id] = f"Error: {responses[i]}"
        else:
            results[model_id] = responses[i]
            
    return results

async def sequential_refinement(prompt: str, api_keys: Dict[str, str]) -> List[Dict[str, str]]:
    """Query models in a chain, each refining the previous output."""
    conversation = [{"role": "user", "content": prompt}]
    current_prompt = prompt
    
    for model_id in MODEL_SEQUENCE:
        key_name = f"{model_id.upper()}_API_KEY"
        if key_name not in api_keys:
            continue

        client = get_client(model_id, api_keys[key_name])
        response = await client.query(current_prompt)
        
        conversation.append({"role": model_id, "content": response})
        
        # Prepare the prompt for the next model in the chain
        current_prompt = f"Original question: {prompt}\n\nPrevious answer to improve:\n{response}"
        
    return conversation

# --- API Endpoint ---
@app.post("/query", response_model=Dict)
async def process_query(request: QueryRequest):
    """
    Main endpoint to process LLM queries.
    - **prompt**: The user's prompt for the LLMs.
    - **password**: The master password to unlock the API keys.
    - **mode**: 'parallel' for simultaneous queries, 'sequential' for a refinement chain.
    """
    api_keys = get_api_keys(request.password)

    if request.mode == "parallel":
        results = await parallel_query(request.prompt, api_keys)
        return {"results": results}
    elif request.mode == "sequential":
        conversation = await sequential_refinement(request.prompt, api_keys)
        return {"conversation": conversation}
    else:
        raise HTTPException(status_code=400, detail="Invalid mode specified.")

@app.get("/", include_in_schema=False)
def root():
    return {"message": "LLM Orchestrator is running. See /docs for API documentation."}
7. Setup Scripts:

llm_orchestrator/scripts/setup_windows.ps1

PowerShell

# PowerShell script to set up the LLM Orchestrator on Windows with WSL2 and Docker
Write-Host "--- LLM Orchestrator Windows Setup ---" -ForegroundColor Yellow

# Step 1: Check for Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not found. Please install Docker Desktop and ensure it's running in WSL2 mode." -ForegroundColor Red
    exit 1
}
Write-Host "Docker found." -ForegroundColor Green

# Step 2: Build the Docker image
Write-Host "Building Docker image 'llm-orchestrator'..."
docker build -t llm-orchestrator .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker build failed." -ForegroundColor Red
    exit 1
}
Write-Host "Docker image built successfully." -ForegroundColor Green

# Step 3: Initialize the secure vault
Write-Host "Initializing secure API key vault..."
docker run -it --rm -v "${PWD}:/app" llm-orchestrator python app/init_vault.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Vault initialization failed." -ForegroundColor Red
    exit 1
}
Write-Host "Vault initialized." -ForegroundColor Green

# Step 4: Provide instructions to run
Write-Host "--- Setup Complete ---" -ForegroundColor Cyan
Write-Host "To run the orchestrator service, use the following command:"
Write-Host "docker run -d --name llm-engine -p 8000:8000 -v `"${PWD}/workspace:/workspace`" -v `"${PWD}/vault.enc:/app/vault.enc`" --rm llm-orchestrator" -ForegroundColor White
llm_orchestrator/scripts/setup_android.sh

Bash

#!/bin/bash
# Bash script to set up the LLM Orchestrator on Android via Termux and proot-distro

echo "--- LLM Orchestrator Android/Termux Setup ---"

# This script assumes you are running it inside a proot-distro environment (e.g., Ubuntu)
# that has Docker installed.

# Check for Docker
if ! command -v docker &> /dev/null
then
    echo "Error: Docker could not be found."
    echo "Please install Docker inside your proot-distro environment."
    echo "Example for Ubuntu: apt update && apt install docker.io"
    exit 1
fi

echo "Docker found."

# Build the Docker image
echo "Building Docker image 'llm-orchestrator'..."
docker build -t llm-orchestrator .
if [ $? -ne 0 ]; then
    echo "Error: Docker build failed."
    exit 1
fi
echo "Docker image built successfully."

# Initialize the secure vault
echo "Initializing secure API key vault..."
# Note: Docker paths must be absolute inside the proot environment
docker run -it --rm -v "$(pwd):/app" llm-orchestrator python app/init_vault.py
if [ $? -ne 0 ]; then
    echo "Error: Vault initialization failed."
    exit 1
fi
echo "Vault initialized."

# Create a shared workspace directory on Android if it doesn't exist
WORKSPACE_DIR="$HOME/storage/shared/LLMWorkspace"
mkdir -p "$WORKSPACE_DIR"
echo "Shared workspace is at: $WORKSPACE_DIR"

echo "--- Setup Complete ---"
echo "To run the orchestrator service, use the following command:"
echo "docker run -d --name llm-engine -p 8000:8000 -v \"$WORKSPACE_DIR:/workspace\" -v \"$(pwd)/vault.enc:/app/vault.enc\" --rm llm-orchestrator"
8. Workspace Directory: Create an empty directory for the volume mount.

Bash

mkdir -p llm_orchestrator/workspace
