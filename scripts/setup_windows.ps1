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
