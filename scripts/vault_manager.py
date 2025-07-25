import glob
import os
import platform
import re

import click
from cryptography.fernet import Fernet, InvalidToken
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from app.key_management import PASSWORD_SALT, VAULT_FILE_PATH, derive_key

console = Console()


def display_export_commands():
    """Securely decrypts the vault and writes the keys to a temporary script."""
    console.print("\n[bold yellow]--- Load Keys into Environment ---[/bold yellow]")
    if not os.path.exists(VAULT_FILE_PATH):
        console.print(
            f"[bold red]Error:[/bold red] Main vault `[cyan]{VAULT_FILE_PATH}[/cyan]` not found."
        )
        return

    try:
        with open(VAULT_FILE_PATH, "rb") as f:
            encrypted_data = f.read()

        password = Prompt.ask(
            "Enter your master password to load the keys", password=True
        )
        key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(key)

        try:
            decrypted_data = cipher.decrypt(encrypted_data).decode("utf-8")
        except InvalidToken:
            console.print("[bold red]Invalid password. Cannot load keys.[/bold red]")
            return

        is_windows = platform.system().lower() == "windows"
        script_filename = "env_loader.ps1" if is_windows else ".env_loader.sh"

        with open(script_filename, "w") as f:
            if is_windows:
                for line in decrypted_data.strip().split("\n"):
                    if line:
                        key, value = line.split("=", 1)
                        f.write(f"$env:{key}='{value}'\n")
            else:
                f.write("#!/bin/bash\n")
                for line in decrypted_data.strip().split("\n"):
                    if line:
                        key, value = line.split("=", 1)
                        f.write(f"export {key}='{value}'\n")

        if not is_windows:
            os.chmod(script_filename, 0o700)

        console.print(
            f"\n[bold green]Success![/bold green] A temporary script has been created at `[cyan]{script_filename}[/cyan]`."
        )
        console.print(
            "\nTo load the keys into your current session, run the following command:"
        )

        if is_windows:
            console.print(f"\n    [bold cyan].\\{script_filename}[/bold cyan]\n")
        else:
            console.print(f"\n    [bold cyan]source ./{script_filename}[/bold cyan]\n")

        console.print(
            "For security, [bold red]delete the script immediately after[/bold red] using it:"
        )
        delete_command = "del" if is_windows else "rm"
        console.print(
            f"\n    [bold cyan]{delete_command} {script_filename}[/bold cyan]\n"
        )

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


def get_all_vaults():
    """Finds all vault files in the current directory."""
    return glob.glob("vault.enc") + glob.glob("side_vault*.enc")


def view_vault_flow():
    """Interactive flow to view the contents of the main vault."""
    console.print("\n[bold yellow]--- View Vault Contents ---[/bold yellow]")
    if not os.path.exists(VAULT_FILE_PATH):
        console.print(
            f"[bold red]Error:[/bold red] Main vault `[cyan]{VAULT_FILE_PATH}[/cyan]` not found."
        )
        return

    try:
        with open(VAULT_FILE_PATH, "rb") as f:
            encrypted_data = f.read()

        password = Prompt.ask(
            "Enter your master password to view the vault", password=True
        )
        key = derive_key(password, PASSWORD_SALT)
        cipher = Fernet(key)

        try:
            decrypted_data = cipher.decrypt(encrypted_data).decode("utf-8")
        except InvalidToken:
            console.print("[bold red]Invalid password. Cannot view vault.[/bold red]")
            return

        table = Table(
            title="Vault Contents", show_header=True, header_style="bold magenta"
        )
        table.add_column("API Key Name", style="cyan")
        table.add_column("Key Value (Redacted)", style="green")

        lines = decrypted_data.strip().split("\n")
        for line in lines:
            match = re.match(r"^(?P<name>\w+)=(?P<value>.+)$", line)
            if match:
                key_name = match.group("name")
                key_value = match.group("value")
                redacted_value = (
                    f"{key_value[:4]}...{key_value[-4:]}"
                    if len(key_value) > 8
                    else key_value
                )
                table.add_row(key_name, redacted_value)

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


def change_password_flow():
    """Interactive flow to change the master password."""
    console.print("\n[bold yellow]--- Change Master Password ---[/bold yellow]")
    if not os.path.exists(VAULT_FILE_PATH):
        console.print(
            f"[bold red]Error:[/bold red] Main vault `[cyan]{VAULT_FILE_PATH}[/cyan]` not found."
        )
        return

    try:
        with open(VAULT_FILE_PATH, "rb") as f:
            encrypted_data = f.read()

        old_password = Prompt.ask("Enter your CURRENT master password", password=True)
        old_key = derive_key(old_password, PASSWORD_SALT)
        cipher = Fernet(old_key)

        try:
            decrypted_data = cipher.decrypt(encrypted_data)
        except InvalidToken:
            console.print(
                "[bold red]Invalid password. Password change failed.[/bold red]"
            )
            return

        console.print("[bold green]Password verified.[/bold green]")
        new_password = Prompt.ask("Enter your NEW master password", password=True)
        new_password_confirm = Prompt.ask(
            "Confirm your NEW master password", password=True
        )

        if new_password != new_password_confirm:
            console.print("[bold red]New passwords do not match. Aborting.[/bold red]")
            return

        new_key = derive_key(new_password, PASSWORD_SALT)
        new_cipher = Fernet(new_key)
        new_encrypted_data = new_cipher.encrypt(decrypted_data)

        with open(VAULT_FILE_PATH, "wb") as f:
            f.write(new_encrypted_data)

        console.print("[bold green]Master password changed successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


def delete_vault_flow():
    """Interactive flow to delete a vault file."""
    console.print("\n[bold yellow]--- Delete a Vault ---[/bold yellow]")
    vaults = get_all_vaults()
    if not vaults:
        console.print("No vaults found to delete.")
        return

    console.print("Available vaults:")
    for i, vault in enumerate(vaults, 1):
        console.print(f"  [{i}] {vault}")

    choice_str = Prompt.ask(
        "Enter the number of the vault to delete (or 'q' to quit)", default="q"
    )
    if choice_str.lower() == "q":
        return

    try:
        choice = int(choice_str) - 1
        if not 0 <= choice < len(vaults):
            console.print("[bold red]Invalid selection.[/bold red]")
            return
    except ValueError:
        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
        return

    vault_to_delete = vaults[choice]

    if not click.confirm(
        f"Are you sure you want to permanently delete '[bold red]{vault_to_delete}[/bold red]'?"
    ):
        console.print("Deletion cancelled.")
        return

    try:
        os.remove(vault_to_delete)
        console.print(
            f"Vault '[bold green]{vault_to_delete}[/bold green]' has been deleted."
        )
    except OSError as e:
        console.print(f"[bold red]Error deleting vault:[/bold red] {e}")


def set_main_vault_flow():
    """Interactive flow to set the main vault."""
    console.print("\n[bold yellow]--- Set Main Vault ---[/bold yellow]")
    side_vaults = glob.glob("side_vault*.enc")

    if not side_vaults:
        console.print("No side vaults found to promote.")
        return

    console.print("Available side vaults:")
    for i, vault in enumerate(side_vaults, 1):
        console.print(f"  [{i}] {vault}")

    choice_str = Prompt.ask(
        "Enter the number of the vault to set as main (or 'q' to quit)", default="q"
    )
    if choice_str.lower() == "q":
        return

    try:
        choice = int(choice_str) - 1
        if not 0 <= choice < len(side_vaults):
            console.print("[bold red]Invalid selection.[/bold red]")
            return
    except ValueError:
        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
        return

    vault_to_promote = side_vaults[choice]

    if os.path.exists("vault.enc"):
        base_name = "side_vault"
        extension = ".enc"
        new_name_for_old_main = f"{base_name}{extension}"
        counter = 2
        while os.path.exists(new_name_for_old_main):
            new_name_for_old_main = f"{base_name}_{counter}{extension}"
            counter += 1
        os.rename("vault.enc", new_name_for_old_main)
        console.print(
            f"Current main vault renamed to `[cyan]{new_name_for_old_main}[/cyan]`."
        )

    os.rename(vault_to_promote, "vault.enc")
    console.print(
        f"Successfully set `[bold green]{vault_to_promote}[/bold green]` as the new main `vault.enc`."
    )


@click.command()
@click.argument("action", required=False)
def manage_vaults(action):
    """
    A menu-driven utility to manage your API key vaults.
    Can also be called with the 'display-keys' action directly.
    """
    if action == "display-keys":
        display_export_commands()
        return

    while True:
        console.print("\n[bold cyan]-- Vault Management --[/bold cyan]")
        console.print("[1] Change Master Password")
        console.print("[2] Delete a Vault")
        console.print("[3] Set Main Vault")
        console.print("[4] View Vault Contents")
        console.print("[q] Quit")

        choice = Prompt.ask("Choose an option", default="q").lower()

        if choice == "1":
            change_password_flow()
        elif choice == "2":
            delete_vault_flow()
        elif choice == "3":
            set_main_vault_flow()
        elif choice == "4":
            view_vault_flow()
        elif choice == "q":
            console.print("Exiting vault manager.")
            break
        else:
            console.print("[bold red]Invalid choice, please try again.[/bold red]")


if __name__ == "__main__":
    manage_vaults()
