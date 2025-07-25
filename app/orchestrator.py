import asyncio
from typing import Any

import yaml
from rich.console import Console

from app.clients import get_client

# --- Configuration ---
MODELS_CONFIG_PATH = "models.yaml"
console = Console()


# --- Load Model Configuration ---
def load_model_config() -> dict[str, Any]:
    """Load model configurations from the YAML file."""
    try:
        with open(MODELS_CONFIG_PATH) as f:
            config = yaml.safe_load(f)
            # Remove system_prompts from the main model config
            if "system_prompts" in config:
                del config["system_prompts"]
            return config
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing {MODELS_CONFIG_PATH}: {e}")


MODEL_CONFIG = load_model_config()


# --- Core Orchestration Logic ---
async def parallel_query(
    prompt: str, api_keys: dict[str, str], model_config: dict[str, Any]
) -> dict[str, str]:
    """
    Query specified models simultaneously.

    Args:
        prompt (str): The prompt to send to the models.
        api_keys (Dict[str, str]): The API keys for the models.
        model_config (Dict[str, Any]): The configuration for the models to query.

    Returns:
        Dict[str, str]: A dictionary of responses from the models.
    """
    tasks = []

    for model_id, config in model_config.items():
        key_name = f"{model_id.upper()}_API_KEY"
        if key_name in api_keys:
            client = get_client(
                client_name=model_id, api_key=api_keys[key_name], model_config=config
            )
            tasks.append(client.query(prompt))

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    model_ids = list(model_config.keys())
    for i, model_id in enumerate(model_ids):
        if i < len(responses):
            if isinstance(responses[i], Exception):
                results[model_id] = f"Error: {responses[i]}"
            else:
                results[model_id] = results[model_id] = responses[i]

    return results


async def sequential_refinement(
    prompt: str, api_keys: dict[str, str], steps: list[dict[str, str]]
) -> list[dict[str, str]]:
    """
    Query models in a chain, with each step using a specific role and persona.

    Args:
        prompt (str): The initial prompt for the chain.
        api_keys (Dict[str, str]): The API keys for the models.
        steps (List[Dict[str, str]]): The steps in the chain.

    Returns:
        List[Dict[str, str]]: The conversation history of the chain.
    """
    conversation = [{"role": "user", "content": prompt}]
    current_prompt = prompt

    for step in steps:
        model_id = step["model"]
        role = step["role"]
        persona = step["persona"]

        key_name = f"{model_id.upper()}_API_KEY"
        if key_name not in api_keys:
            # Skip step if API key is missing
            conversation.append(
                {
                    "role": model_id,
                    "content": f"Error: API key for {model_id} not found.",
                }
            )
            continue

        # Construct the prompt for the current step
        if len(conversation) == 1:  # First step
            step_prompt = f"As a {persona}, your role is to {role}. Your first task is to address the following prompt:\n\n{current_prompt}"
        else:
            previous_response = conversation[-1]["content"]
            step_prompt = f"You are a {persona}, and your role is to {role} the following text. Continue the chain of thought.\n\nPrevious response:\n{previous_response}\n\nYour task is to now {role} this response."

        config = MODEL_CONFIG.get(model_id, {})
        client = get_client(
            client_name=model_id, api_key=api_keys[key_name], model_config=config
        )

        console_name = f"{model_id} ({role}/{persona})"
        response = await client.query(step_prompt)

        conversation.append({"role": console_name, "content": response})

        # The entire conversation history is not passed, only the last response.
        # This can be changed for a more conversational chain.
        current_prompt = response

    return conversation


def get_system_prompts() -> dict[str, str]:
    """
    Load system prompts from the models YAML file.

    Returns:
        Dict[str, str]: A dictionary of system prompts.
    """
    try:
        with open(MODELS_CONFIG_PATH) as f:
            config = yaml.safe_load(f)
            return config.get("system_prompts", {})
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing {MODELS_CONFIG_PATH}: {e}")
