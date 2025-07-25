from typing import Any

import anthropic
import google.generativeai as genai
from mistralai import Mistral as MistralAIClient
from openai import OpenAI


class BaseClient:
    def __init__(self, api_key: str, model_config: dict[str, Any]):
        self.api_key = api_key
        self.model_config = model_config
        self.model_name = model_config.get("model", "default")

    async def query(self, prompt: str):
        raise NotImplementedError("Query method must be implemented by subclasses.")


class AnthropicClient(BaseClient):
    def __init__(self, api_key: str, model_config: dict[str, Any]):
        super().__init__(api_key, model_config)
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def query(self, prompt: str):
        """Query the Anthropic model asynchronously."""
        print(f"Querying Anthropic ({self.model_name})...")
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.model_config.get("max_tokens", 1024),
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"An error occurred while querying Anthropic: {e}")
            return f"Error: Could not get response from Anthropic. Details: {e}"


class GeminiClient(BaseClient):
    def __init__(self, api_key: str, model_config: dict[str, Any]):
        super().__init__(api_key, model_config)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def query(self, prompt: str):
        """Query the Gemini model asynchronously."""
        print(f"Querying Gemini ({self.model_name})...")
        try:
            temperature = self.model_config.get("temperature")
            generation_config = genai.types.GenerationConfig(temperature=temperature)

            response = await self.model.generate_content_async(
                prompt, generation_config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"An error occurred while querying Gemini: {e}")
            return f"Error: Could not get response from Gemini. Details: {e}"


class DeepSeekClient(BaseClient):
    def __init__(self, api_key: str, model_config: dict[str, Any]):
        super().__init__(api_key, model_config)
        self.client = OpenAI(
            api_key=self.api_key, base_url="https://api.deepseek.com/v1"
        )

    async def query(self, prompt: str):
        """Query the DeepSeek model asynchronously."""
        print(f"Querying DeepSeek ({self.model_name})...")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name, messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred while querying DeepSeek: {e}")
            return f"Error: Could not get response from DeepSeek. Details: {e}"


class MistralClient(BaseClient):
    def __init__(self, api_key: str, model_config: dict[str, Any]):
        super().__init__(api_key, model_config)
        self.client = MistralAIClient(api_key=self.api_key)

    async def query(self, prompt: str):
        """Query the Mistral model asynchronously."""
        print(f"Querying Mistral ({self.model_name})...")
        try:
            response = self.client.chat.complete(
                model=self.model_name, messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred while querying Mistral: {e}")
            return f"Error: Could not get response from Mistral. Details: {e}"


def get_client(client_name: str, api_key: str, model_config: dict[str, Any]):
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
    return client_class(api_key=api_key, model_config=model_config)
