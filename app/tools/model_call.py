"""
Model call tool for executing LLM API calls.
This is the core tool that handles communication with various LLM providers.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from rich.console import Console

from .base import BaseTool
from ..clients import get_client
from ..key_management import get_api_keys

console = Console()


class ModelCallTool(BaseTool):
    """
    Tool for making API calls to LLM providers.

    Required inputs:
    - provider: The LLM provider (e.g., 'gemini', 'anthropic', 'deepseek', 'mistral')
    - model: The specific model to use
    - prompt: The prompt to send to the model

    Optional inputs:
    - max_tokens: Maximum tokens in response
    - temperature: Sampling temperature
    """

    def __init__(self, vault_password: Optional[str] = None):
        """
        Initialize the model call tool.
        
        Args:
            vault_password: Password for decrypting API keys. If None, will prompt when needed.
        """
        self.vault_password = vault_password
        self._api_keys: Optional[Dict[str, str]] = None

    def validate_inputs(self, **kwargs) -> None:
        """Validate required inputs for model call."""
        required_fields = ["provider", "model", "prompt"]
        missing_fields = [field for field in required_fields if field not in kwargs]

        if missing_fields:
            raise ValueError(
                f"Missing required fields for model_call: {missing_fields}"
            )

        # Validate provider
        supported_providers = ["anthropic", "gemini", "deepseek", "mistral"]
        provider = kwargs.get("provider", "").lower()
        if provider not in supported_providers:
            raise ValueError(
                f"Unsupported provider '{provider}'. Supported: {supported_providers}"
            )

    def _get_api_keys(self) -> Dict[str, str]:
        """Get API keys from vault or environment variables."""
        if self._api_keys is None:
            if self.vault_password is None:
                # Try to get keys from environment variables
                env_keys = {}
                for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "MISTRAL_API_KEY"]:
                    if key in os.environ:
                        env_keys[key] = os.environ[key]
                
                if env_keys:
                    console.print(f"✅ Found {len(env_keys)} API keys in environment", style="green")
                    self._api_keys = env_keys
                    return self._api_keys
                else:
                    console.print(
                        "⚠️  No vault password provided and no API keys in environment, using simulation mode",
                        style="yellow",
                    )
                    return {}

            try:
                self._api_keys = get_api_keys(self.vault_password)
                console.print("✅ API keys loaded from vault", style="green")
            except Exception as e:
                console.print(f"❌ Failed to load API keys: {str(e)}", style="red")
                console.print("🔄 Falling back to simulation mode", style="yellow")
                return {}

        return self._api_keys or {}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute a model call with the given parameters.

        Args:
            **kwargs: Model call parameters (provider, model, prompt, etc.)

        Returns:
            Dict containing the model response and metadata
        """
        # Validate inputs
        self.validate_inputs(**kwargs)

        provider = kwargs.get("provider").lower()
        model = kwargs.get("model")
        prompt = kwargs.get("prompt")

        console.print(f"🤖 Calling {provider}/{model}...", style="blue")

        # Get API keys
        api_keys = self._get_api_keys()

        # Check if we have the required API key
        provider_key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
        }

        required_key = provider_key_map.get(provider)
        if not api_keys or required_key not in api_keys:
            # Simulation mode
            console.print(
                f"🔄 No API key for {provider}, using simulation", style="yellow"
            )
            response_text = (
                f"[SIMULATED {provider}/{model}] Response to: {prompt[:50]}..."
            )
            return {
                "output": response_text,
                "provider": provider,
                "model": model,
                "simulated": True,
            }

        # Real API call
        try:
            # Prepare model config
            model_config = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", 1024),
                "temperature": kwargs.get("temperature", 0.7),
            }

            # Get client and make async call
            client = get_client(provider, api_keys[required_key], model_config)

            # Run the async query
            response_text = asyncio.run(client.query(prompt))

            console.print(f"✅ Received response from {provider}/{model}", style="green")

            return {
                "output": response_text,
                "provider": provider,
                "model": model,
                "simulated": False,
                "token_count": len(response_text.split()),  # Rough estimate
            }

        except Exception as e:
            console.print(f"❌ API call failed: {str(e)}", style="red")
            console.print("🔄 Falling back to simulation", style="yellow")

            # Fallback to simulation
            response_text = f"[SIMULATED {provider}/{model} - API Error] Response to: {prompt[:50]}..."
            return {
                "output": response_text,
                "provider": provider,
                "model": model,
                "simulated": True,
                "error": str(e),
            }
