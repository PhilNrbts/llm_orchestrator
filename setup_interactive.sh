#!/bin/bash

# Color definitions for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Introduction ---
echo -e "${GREEN}--- LLM Orchestrator Setup ---${NC}"
echo "This script will guide you through setting up the LLM Orchestrator."
echo "It will check for prerequisites, build the required Docker image, and"
echo "help you create a secure vault for your API keys."
echo

# --- Prerequisite Check: Docker ---
echo -n "Checking for Docker..."
if ! command -v docker &> /dev/null; then
    echo -e " ${RED}Not Found.${NC}"
    echo -e "${RED}Error: Docker is not installed or not in your PATH.${NC}"
    echo "Please install Docker Desktop (Windows/Mac) or Docker Engine (Linux) to continue."
    exit 1
fi
echo -e " ${GREEN}OK.${NC}"
echo

# --- Step 1: Build Docker Image ---
echo -e "${YELLOW}ACTION:${NC} The Docker image 'llm-orchestrator' needs to be built. Build it now? (Y/n): "
read -p "" response
response=${response,,} # tolower
if [[ "$response" =~ ^(yes|y|)$ ]]; then
    echo "Building Docker image... (This may take a few minutes)"
    docker build -t llm-orchestrator .
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Docker build failed. Please check the output above for errors.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Docker image built successfully.${NC}"
else
    echo "Skipping Docker build. Please ensure the image 'llm-orchestrator:latest' exists."
fi
echo

# --- Step 2: Initialize Secure Vault ---
echo -e "${YELLOW}ACTION:${NC} Do you want to set up the secure API key vault now? (Y/n): "
read -p "" response
response=${response,,} # tolower
if [[ "$response" =~ ^(yes|y|)$ ]]; then
    echo "The next step will run an interactive script inside a temporary Docker container."
    echo "You will be prompted to enter your API keys and a master password for the vault."
    echo "Your password is never stored, and the keys are saved in an encrypted 'vault.enc' file."
    echo
    read -p "Press [Enter] to continue..."

    docker run -it --rm --entrypoint python -v "${PWD}:/app" -w /app llm-orchestrator app/init_vault.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Vault initialization failed or was cancelled.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Secure vault 'vault.enc' has been created successfully.${NC}"
else
    echo "Skipping vault setup. Please ensure a valid 'vault.enc' file exists before running the service."
fi
echo

# --- Completion ---
echo -e "${GREEN}--- Setup Complete ---${NC}"
echo
echo "You are ready to go!"
echo

# --- Step 3: Run the Service ---
echo -e "${YELLOW}ACTION:${NC} Would you like to start the LLM Orchestrator service now? (Y/n): "
read -p "" response
response=${response,,} # tolower
if [[ "$response" =~ ^(yes|y|)$ ]]; then
    echo "Starting the container in the background..."
    docker run -d --name llm-engine -v "${PWD}/vault.enc:/vault.enc" -v "${PWD}/models.yaml:/models.yaml" -v "${PWD}/workspace:/workspace" --rm llm-orchestrator
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to start the container. Please check the output above.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Service started successfully!${NC}"
    echo
    echo -e "${YELLOW}Next Step: Use the CLI${NC}"
    echo "You can now use the LLM Orchestrator CLI. Try running:"
    echo
    cat <<'EOF'
  docker exec -it llm-engine python -m app.main --help
EOF
    echo
else
    echo "You can start the service later with the following command:"
    echo -e "  docker run -d --name llm-engine -v "\${PWD}/vault.enc:/vault.enc" -v "\${PWD}/models.yaml:/models.yaml" -v "\${PWD}/workspace:/workspace" --rm llm-orchestrator"
    echo
fi

exit 0
