import os
import asyncio
import hashlib
import base64
import yaml
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from cryptography.fernet import Fernet, InvalidToken

from app.clients import get_client

# --- Configuration ---
VAULT_FILE_PATH = os.environ.get("VAULT_FILE_PATH", "/app/vault.enc")
MODELS_CONFIG_PATH = os.environ.get("MODELS_CONFIG_PATH", "/app/../models.yaml")
PASSWORD_SALT = b"a-secure-random-salt-should-be-used-here"

# --- Load Model Configuration ---
def load_model_config() -> Dict[str, Any]:
    """Load model configurations from the YAML file."""
    try:
        with open(MODELS_CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # In a real app, you might have a default config or a more robust error handling
        return {}
    except yaml.YAMLError as e:
        # Handle YAML parsing errors
        raise RuntimeError(f"Error parsing {MODELS_CONFIG_PATH}: {e}")

MODEL_CONFIG = load_model_config()
MODEL_SEQUENCE = list(MODEL_CONFIG.keys())


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
    
    for model_id, config in MODEL_CONFIG.items():
        key_name = f"{model_id.upper()}_API_KEY"
        if key_name in api_keys:
            client = get_client(
                client_name=model_id,
                api_key=api_keys[key_name],
                model_config=config
            )
            tasks.append(client.query(prompt))

    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = {}
    model_ids = list(MODEL_CONFIG.keys())
    for i, model_id in enumerate(model_ids):
        if i < len(responses):
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

        config = MODEL_CONFIG.get(model_id, {})
        client = get_client(
            client_name=model_id,
            api_key=api_keys[key_name],
            model_config=config
        )
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