import glob
import json
import os

import pytest
import yaml
from click.testing import CliRunner
from cryptography.fernet import Fernet

from app.key_management import PASSWORD_SALT, derive_key
from app.main import cli


# --- A Simple Mock Client ---
class MockSuccessfulClient:
    async def query(self, prompt, **kwargs):
        final_prompt = prompt.split("--- New Prompt ---\n")[-1]
        return f"Mocked response to '{final_prompt}'"


# --- Fixtures ---


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_vault(tmp_path):
    vault_path = tmp_path / "test_vault.enc"
    password = "testpassword"
    keys = "GEMINI_API_KEY=fake_gemini_key\nANTHROPIC_API_KEY=fake_anthropic_key"
    encryption_key = derive_key(password, PASSWORD_SALT)
    cipher = Fernet(encryption_key)
    encrypted_data = cipher.encrypt(keys.encode("utf-8"))
    with open(vault_path, "wb") as f:
        f.write(encrypted_data)
    return vault_path, password


@pytest.fixture(autouse=True)
def mock_all_clients(monkeypatch):
    """
    Mocks the get_client factory to return a simple, successful mock client
    for all tests. This is a simpler and more robust mocking strategy.
    """

    def fake_get_client(client_name, api_key, model_config):
        return MockSuccessfulClient()

    monkeypatch.setattr("app.orchestrator.get_client", fake_get_client)

    async def fake_parallel_query(prompt, api_keys, model_config):
        return {
            model: f"Response from {model} for '{prompt}'"
            for model in model_config.keys()
        }

    monkeypatch.setattr("app.orchestrator.parallel_query", fake_parallel_query)


@pytest.fixture(autouse=True)
def cleanup_conversations():
    yield
    files = glob.glob("conversations/chat_*.json")
    for f in files:
        os.remove(f)


# --- Tests ---


def test_config_set_main_with_specific_model(runner):
    config_path = "config.yaml"
    with open(config_path) as f:
        original_config = yaml.safe_load(f)

    runner.invoke(cli, ["config", "set-main", "anthropic", "claude-3-haiku-20240307"])

    with open(config_path) as f:
        updated_config = yaml.safe_load(f)
    assert updated_config["main_llm"]["model"] == "claude-3-haiku-20240307"

    with open(config_path, "w") as f:
        yaml.dump(original_config, f)


def test_run_parallel(runner, mock_vault):
    vault_path, password = mock_vault
    os.environ["VAULT_FILE_PATH"] = str(vault_path)

    result = runner.invoke(
        cli,
        [
            "run",
            "-p",
            "test prompt",
            "--model",
            "gemini",
            "--model",
            "anthropic-haiku",
            "--password",
            password,
        ],
    )

    assert result.exit_code == 0
    assert "Response from gemini" in result.output
    assert "Response from anthropic-haiku" in result.output

    del os.environ["VAULT_FILE_PATH"]


def test_interactive_chat_session(runner, mock_vault, monkeypatch):
    vault_path, password = mock_vault
    os.environ["VAULT_FILE_PATH"] = str(vault_path)
    monkeypatch.setattr("app.main.get_password", lambda x: password)

    result = runner.invoke(cli, input="Hello\nexit\n")

    assert result.exit_code == 0
    assert "Mocked response to 'Hello'" in result.output
    assert "Conversation saved" in result.output

    del os.environ["VAULT_FILE_PATH"]


def test_interactive_chat_model_switching(runner, mock_vault, monkeypatch):
    vault_path, password = mock_vault
    os.environ["VAULT_FILE_PATH"] = str(vault_path)
    monkeypatch.setattr("app.main.get_password", lambda x: password)

    user_choices = ["1", "y", "2", "n"]

    def mock_ask(prompt_text, **kwargs):
        if "choices" in kwargs:
            return user_choices.pop(0)
        # This simulates the user typing different things for each free-form prompt
        # It's a bit brittle but works for this test case
        if "Hello" in prompt_text:
            return "Hello"
        if "Continue" in prompt_text:
            return "Continue"
        if "Last message" in prompt_text:
            return "Last message"
        return "Simulated chat input"

    monkeypatch.setattr("rich.prompt.Prompt.ask", mock_ask)

    user_input = "Hello\n/changeProvider\nContinue\n/changeModel\nLast message\nexit\n"
    result = runner.invoke(cli, input=user_input)

    assert result.exit_code == 0
    assert "Switched model to: anthropic (claude-3-5-sonnet-20240620)" in result.output
    assert "Switched model to: anthropic (claude-3-haiku-20240307)" in result.output

    saved_files = glob.glob("conversations/chat_*.json")
    assert len(saved_files) == 1
    with open(saved_files[0]) as f:
        history = json.load(f)

    assert len(history) == 6
    assert history[5]["role"] == "anthropic/claude-3-haiku-20240307"

    del os.environ["VAULT_FILE_PATH"]
