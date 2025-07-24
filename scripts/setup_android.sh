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
echo "Building Docker image 'llm-orchestrator'...
"docker build -t llm-orchestrator .
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
