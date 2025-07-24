import pytest
import base64
from app.key_management import derive_key, PASSWORD_SALT
from app.main import parse_step
from scripts.init_vault import parse_api_keys

# --- Test Key Derivation ---

def test_derive_key_is_deterministic():
    """Ensures the same password and salt produce the same key."""
    key1 = derive_key("test_password", PASSWORD_SALT)
    key2 = derive_key("test_password", PASSWORD_SALT)
    assert key1 == key2
    assert isinstance(key1, bytes)

def test_derive_key_different_passwords():
    """Ensures different passwords produce different keys."""
    key1 = derive_key("test_password_1", PASSWORD_SALT)
    key2 = derive_key("test_password_2", PASSWORD_SALT)
    assert key1 != key2

def test_derive_key_is_valid_base64():
    """Checks if the derived key is valid Base64."""
    key = derive_key("test_password", PASSWORD_SALT)
    try:
        base64.urlsafe_b64decode(key)
    except (ValueError, TypeError):
        pytest.fail("The derived key is not valid URL-safe Base64")

# --- Test Step Parser ---

def test_parse_step_valid():
    """Tests the step parser with a valid string."""
    step_str = "Critique>/Developer)-gemini"
    expected = {"role": "Critique", "persona": "Developer", "model": "gemini"}
    assert parse_step(step_str) == expected

def test_parse_step_invalid_format():
    """Tests that the step parser returns None for invalid formats."""
    assert parse_step("Critique/Developer-gemini") is None
    assert parse_step("Critique>/Developer") is None
    assert parse_step("Critique>") is None

# --- Test API Key Parser ---

def test_parse_api_keys_valid():
    """Tests the API key parser with a valid block of text."""
    text_block = """
    GEMINI_API_KEY=key123
    ANTHROPIC_API_KEY=key456
    """
    expected = {
        "GEMINI_API_KEY": "key123",
        "ANTHROPIC_API_KEY": "key456"
    }
    assert parse_api_keys(text_block) == expected

def test_parse_api_keys_invalid_name():
    """Tests that the parser raises an error for a key name not ending in _API_KEY."""
    text_block = "INVALID_KEY=key123"
    with pytest.raises(ValueError, match="All keys must end with '_API_KEY'"):
        parse_api_keys(text_block)

def test_parse_api_keys_invalid_format():
    """Tests that the parser raises an error for lines not in KEY=value format."""
    text_block = "GEMINI_API_KEY"
    with pytest.raises(ValueError, match="Invalid format for line"):
        parse_api_keys(text_block)

def test_parse_api_keys_empty_input():
    """Tests that the parser returns an empty dict for empty or whitespace-only input."""
    assert parse_api_keys("") == {}
    assert parse_api_keys("   \n   ") == {}
