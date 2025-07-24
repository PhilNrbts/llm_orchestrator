# Legacy Architecture: Docker & Web API

This document archives the original architecture for this project, which was designed as a containerized web service. This approach has been deprecated in favor of a simpler, direct command-line interface to focus on core functionality.

## Original Concept

The project was initially a secure, containerized, and cross-platform framework to interact with multiple Large Language Models (LLMs). It was designed to run within a Docker container, accessible via a FastAPI web server.

### Original Features

-   **Secure API Key Storage**: Used PBKDF2 for key derivation and Fernet (AES-128-CBC) for encrypting API keys.
-   **Dual Execution Modes**: Flexible parallel or sequential processing of prompts.
-   **Containerized with Docker**: Easy to set up and run consistently on any system with Docker support.
-   **Web API**: Exposed a REST API using FastAPI for integration.

## Legacy Usage (Web API)

Interaction was done via an HTTP client like `curl`.

**Parallel Query Example:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "password": "your-secret-password",
    "mode": "parallel"
  }'
```
