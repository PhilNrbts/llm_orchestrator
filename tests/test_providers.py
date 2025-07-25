import pytest

from app.clients import get_client
from app.key_management import get_api_keys
from app.orchestrator import load_model_config

# Load model configurations
MODEL_CONFIG = load_model_config()

# Create a list of all provider-model combinations for parameterization
ALL_MODELS = []
for provider, config in MODEL_CONFIG.items():
    if provider != "system_prompts":
        for model in config.get("models", []):
            ALL_MODELS.append((provider, model["name"]))


@pytest.mark.parametrize("provider, model_name", ALL_MODELS)
@pytest.mark.asyncio
async def test_provider_model_generation(provider, model_name):
    """
    Test that each configured provider and model can generate text.
    """
    # This test requires a master password to be set as an environment variable
    # for non-interactive testing.
    import os

    password = os.environ.get("MASTER_PASSWORD")
    if not password:
        pytest.skip("MASTER_PASSWORD environment variable not set.")

    api_keys = get_api_keys(password)
    provider_config = MODEL_CONFIG.get(provider)
    api_key_name = provider_config.get("api_key_name")
    api_key = api_keys.get(api_key_name)

    if not api_key:
        pytest.fail(
            f"API key '{api_key_name}' not found in vault for provider '{provider}'."
        )

    model_details = next(
        (m for m in provider_config["models"] if m["name"] == model_name), None
    )
    if not model_details:
        pytest.fail(f"Model '{model_name}' not found for provider '{provider}'.")

    model_config_for_client = model_details.copy()
    model_config_for_client["model"] = model_name

    client = get_client(
        client_name=provider, api_key=api_key, model_config=model_config_for_client
    )

    prompt = "hello"
    response = await client.query(prompt)

    assert isinstance(response, str)
    assert len(response) > 0
    assert not response.startswith("Error:")
