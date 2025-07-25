import os
import platform
import re

import click
from cryptography.fernet import Fernet
from rich.console import Console

from app.key_management import PASSWORD_SALT, VAULT_FILE_PATH, derive_key

console = Console()


def handle_existing_vault():
    """Checks for and handles an existing vault file."""
    if not os.path.exists(VAULT_FILE_PATH):
        return True

    console.print(
        f"\n[bold yellow]Warning:[/bold yellow] An existing vault was found at `[cyan]{VAULT_FILE_PATH}[/cyan]`."
    )
    if not click.confirm("Do you want to create a new vault and rename the old one?"):
        console.print("Aborting vault setup.")
        return False

    base_name = "side_vault"
    extension = ".enc"
    new_name = f"{base_name}{extension}"
    counter = 2
    while os.path.exists(new_name):
        new_name = f"{base_name}_{counter}{extension}"
        counter += 1

    try:
        os.rename(VAULT_FILE_PATH, new_name)
        console.print(f"The old vault has been renamed to `[cyan]{new_name}[/cyan]`.")
        return True
    except OSError as e:
        console.print(
            f"[bold red]Error:[/bold red] Could not rename the old vault: {e}"
        )
        return False


def parse_api_keys(text_block: str) -> dict:
    """Parses a block of text for API keys and returns a dictionary."""
    keys = {}
    lines = text_block.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r"^(?P<name>\w+)=(?P<key>.+)$", line)
        if not match:
            raise ValueError(
                f"Invalid format for line: '{line}'. Expected format: KEY_NAME=key_value"
            )

        key_name = match.group("name")
        key_value = match.group("key")

        if not key_name.endswith("_API_KEY"):
            raise ValueError(
                f"Invalid key name: '{key_name}'. All keys must end with '_API_KEY'."
            )

        keys[key_name] = key_value

    return keys


def display_export_commands(api_keys: dict):
    """Displays the commands to export API keys as environment variables."""
    console.print(
        "\n[bold cyan]To load these keys into your current terminal session, copy and paste the commands below:[/bold cyan]"
    )

    is_windows = platform.system().lower() == "windows"

    if is_windows:
        console.print("[italic](Detected Windows PowerShell)[/italic]")
        for name, key in api_keys.items():
            console.print(f"$env:{name}='{key}'")
    else:
        console.print("[italic](Detected Linux/macOS)[/italic]")
        for name, key in api_keys.items():
            console.print(f"export {name}='{key}'")


@click.command()
def init_vault():
    """
    Initializes or overwrites the encrypted API key vault.
    """
    console.print("[bold yellow]Welcome to the vault setup utility.[/bold yellow]")

    if not handle_existing_vault():
        return

    console.print(
        "\nPlease paste your API keys below in the format `NAME_API_KEY=value`."
    )
    console.print("End your paste with Ctrl+D (on Unix) or Ctrl+Z+Enter (on Windows).")

    try:
        text_block = click.edit()
        if not text_block:
            console.print("[bold red]No input received. Aborting.[/bold red]")
            return

        api_keys = parse_api_keys(text_block)

        if not api_keys:
            console.print("[bold red]No valid keys were parsed. Aborting.[/bold red]")
            return

        detected_key_names = ", ".join(
            [k.replace("_API_KEY", "") for k in api_keys.keys()]
        )
        if not click.confirm(
            f"\n[bold green]Success![/bold green] {len(api_keys)} keys were detected: {detected_key_names}.\nIs that correct?"
        ):
            console.print("Aborting vault setup.")
            return

        password = click.prompt(
            "Enter a master password for the vault",
            hide_input=True,
            confirmation_prompt=True,
        )

        encryption_key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(encryption_key)

        plaintext_keys = "\n".join([f"{name}={key}" for name, key in api_keys.items()])
        encrypted_data = cipher.encrypt(plaintext_keys.encode("utf-8"))

        with open(VAULT_FILE_PATH, "wb") as f:
            f.write(encrypted_data)

        console.print(
            f"\n[bold green]Vault created successfully at '{VAULT_FILE_PATH}'![/bold green]"
        )
        console.print(
            "[italic]Note: The main application will automatically load keys from this vault when you run it.[/italic]"
        )

        if click.confirm(
            "\nDo you want to load these keys into your environment for the current session?"
        ):
            display_export_commands(api_keys)

    except ValueError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}")


if __name__ == "__main__":
    init_vault()
