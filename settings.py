import subprocess
import sys

import click
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def run_script(script_name, args=None):
    """Runs a Python script as a module, with optional arguments."""
    command = [sys.executable, "-m", script_name]
    if args:
        command.extend(args)
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        # The error is printed within the called script, so we just note that it failed.
        console.print(
            f"\n[bold red]The script '{script_name}' exited with an error.[/bold red]"
        )
    except FileNotFoundError:
        console.print(
            f"\n[bold red]Error:[/bold red] Could not find the Python interpreter '{sys.executable}'."
        )


@click.command()
def settings():
    """
    A master menu for managing project settings.
    """
    while True:
        console.print("\n[bold cyan]-- Project Settings --[/bold cyan]")
        console.print("[1] Initialize a new vault")
        console.print("[2] Manage existing vaults")
        console.print("[3] Load Keys into Environment")
        console.print("[q] Quit")

        choice = Prompt.ask("Choose an option", default="q").lower()

        if choice == "1":
            run_script("scripts.init_vault")
        elif choice == "2":
            run_script("scripts.vault_manager")
        elif choice == "3":
            # We can't truly export variables to the parent shell,
            # so we call a function within the vault manager to *display* the commands.
            run_script("scripts.vault_manager", args=["display-keys"])
        elif choice == "q":
            console.print("Exiting settings.")
            break
        else:
            console.print("[bold red]Invalid choice, please try again.[/bold red]")


if __name__ == "__main__":
    settings()
