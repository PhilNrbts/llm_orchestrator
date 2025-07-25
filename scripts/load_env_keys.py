#!/usr/bin/env python3
"""
Utility script to load API keys from the encrypted vault into environment variables.
This is useful for testing and development when you want to use the real APIs.

Usage:
    # Load keys and run a command
    python scripts/load_env_keys.py python scripts/run_workflow.py sequential_elaboration user_prompt="test"
    
    # Just export the keys (for bash)
    eval $(python scripts/load_env_keys.py --export)
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.key_management import get_api_keys
from rich.console import Console

console = Console()


def load_keys_to_env(vault_password: str) -> dict:
    """Load API keys from vault and set them as environment variables."""
    try:
        api_keys = get_api_keys(vault_password)
        
        # Set environment variables
        for key, value in api_keys.items():
            os.environ[key] = value
            
        console.print(f"✅ Loaded {len(api_keys)} API keys into environment", style="green")
        return api_keys
        
    except FileNotFoundError:
        console.print("❌ Vault file not found. Please run scripts/init_vault.py first", style="red")
        return {}
    except ValueError as e:
        console.print(f"❌ {str(e)}", style="red")
        return {}
    except Exception as e:
        console.print(f"❌ Failed to load keys: {str(e)}", style="red")
        return {}


def main():
    if len(sys.argv) < 2:
        console.print("Usage:")
        console.print("  python scripts/load_env_keys.py <command> [args...]")
        console.print("  python scripts/load_env_keys.py --export")
        console.print("\nExamples:")
        console.print("  python scripts/load_env_keys.py python scripts/run_workflow.py sequential_elaboration user_prompt='test'")
        console.print("  eval $(python scripts/load_env_keys.py --export)")
        return

    # Get vault password
    vault_password = getpass.getpass("Enter vault password: ")
    
    # Load keys
    api_keys = load_keys_to_env(vault_password)
    
    if not api_keys:
        console.print("❌ No API keys loaded, exiting", style="red")
        sys.exit(1)

    if sys.argv[1] == "--export":
        # Export format for bash
        for key, value in api_keys.items():
            print(f"export {key}='{value}'")
    else:
        # Run the command with loaded environment
        command = sys.argv[1:]
        console.print(f"🚀 Running command with loaded API keys: {' '.join(command)}", style="blue")
        
        try:
            result = subprocess.run(command, env=os.environ.copy())
            sys.exit(result.returncode)
        except KeyboardInterrupt:
            console.print("\n⚠️  Command interrupted", style="yellow")
            sys.exit(130)
        except Exception as e:
            console.print(f"❌ Failed to run command: {str(e)}", style="red")
            sys.exit(1)


if __name__ == "__main__":
    main()
