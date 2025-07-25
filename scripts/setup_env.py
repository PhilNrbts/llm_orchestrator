#!/usr/bin/env python3
"""
Environment setup utility for the LLM orchestrator.
This script helps you set up API keys in your environment from the vault or manually.
"""

import os
import sys
import getpass
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.key_management import get_api_keys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


def check_vault_exists() -> bool:
    """Check if vault.enc exists."""
    vault_path = os.environ.get("VAULT_FILE_PATH", "vault.enc")
    return os.path.exists(vault_path)


def check_env_keys() -> dict:
    """Check which API keys are already in environment."""
    keys = ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "MISTRAL_API_KEY"]
    found_keys = {}
    for key in keys:
        if key in os.environ:
            found_keys[key] = "***" + os.environ[key][-4:] if len(os.environ[key]) > 4 else "***"
    return found_keys


def load_from_vault() -> bool:
    """Load API keys from vault."""
    if not check_vault_exists():
        console.print("❌ No vault.enc file found", style="red")
        console.print("Run 'python scripts/init_vault.py' to create one", style="yellow")
        return False
    
    try:
        vault_password = getpass.getpass("Enter vault password: ")
        api_keys = get_api_keys(vault_password)
        
        # Set environment variables
        for key, value in api_keys.items():
            os.environ[key] = value
        
        console.print(f"✅ Loaded {len(api_keys)} API keys from vault", style="green")
        
        # Show export commands for bash
        console.print("\n📋 To set these in your shell, run:", style="blue")
        console.print("eval $(python scripts/load_env_keys.py --export)", style="cyan")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Failed to load from vault: {str(e)}", style="red")
        return False


def manual_setup() -> bool:
    """Manually set up API keys."""
    console.print("🔧 Manual API Key Setup", style="blue")
    console.print("Enter your API keys (press Enter to skip):")
    
    keys_to_set = {
        "ANTHROPIC_API_KEY": "Anthropic API Key",
        "GEMINI_API_KEY": "Google Gemini API Key", 
        "DEEPSEEK_API_KEY": "DeepSeek API Key",
        "MISTRAL_API_KEY": "Mistral API Key"
    }
    
    set_count = 0
    export_commands = []
    
    for env_key, description in keys_to_set.items():
        current_value = os.environ.get(env_key, "")
        if current_value:
            console.print(f"✅ {description}: Already set (***{current_value[-4:]})", style="green")
            continue
            
        value = Prompt.ask(f"{description}", default="", show_default=False)
        if value.strip():
            os.environ[env_key] = value.strip()
            export_commands.append(f"export {env_key}='{value.strip()}'")
            set_count += 1
            console.print(f"✅ Set {env_key}", style="green")
    
    if set_count > 0:
        console.print(f"\n✅ Set {set_count} API keys in current session", style="green")
        
        if export_commands:
            console.print("\n📋 To set these in your shell permanently, add to ~/.bashrc or ~/.zshrc:", style="blue")
            for cmd in export_commands:
                console.print(f"  {cmd}", style="cyan")
        
        return True
    else:
        console.print("⚠️  No API keys were set", style="yellow")
        return False


def main():
    console.print(Panel.fit("🔧 LLM Orchestrator Environment Setup", style="blue"))
    
    # Check current status
    vault_exists = check_vault_exists()
    env_keys = check_env_keys()
    
    console.print("\n📊 Current Status:")
    console.print(f"  • Vault file (vault.enc): {'✅ Found' if vault_exists else '❌ Not found'}")
    console.print(f"  • Environment API keys: {len(env_keys)} found")
    
    if env_keys:
        for key, masked_value in env_keys.items():
            console.print(f"    - {key}: {masked_value}")
    
    if len(env_keys) >= 1:
        console.print("\n✅ You already have API keys in your environment!", style="green")
        console.print("You can run workflows directly:", style="green")
        console.print("  python scripts/run_workflow.py sequential_elaboration user_prompt='test'", style="cyan")
        return
    
    console.print("\n🎯 Setup Options:")
    
    if vault_exists:
        console.print("1. Load API keys from encrypted vault")
        console.print("2. Set API keys manually")
        console.print("3. Exit")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            if load_from_vault():
                console.print("\n🎉 Setup complete! You can now run workflows.", style="green")
            else:
                console.print("\n❌ Vault loading failed. Try manual setup.", style="red")
        elif choice == "2":
            manual_setup()
        else:
            console.print("👋 Goodbye!", style="blue")
            return
    else:
        console.print("No vault found. You can:")
        console.print("1. Set API keys manually for this session")
        console.print("2. Create a vault first (run: python scripts/init_vault.py)")
        console.print("3. Exit")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            manual_setup()
        elif choice == "2":
            console.print("Run: python scripts/init_vault.py", style="cyan")
        else:
            console.print("👋 Goodbye!", style="blue")
            return
    
    # Test the setup
    if len(check_env_keys()) > 0:
        console.print("\n🧪 Test your setup:", style="blue")
        console.print("  python scripts/run_workflow.py sequential_elaboration user_prompt='Hello world'", style="cyan")


if __name__ == "__main__":
    main()
