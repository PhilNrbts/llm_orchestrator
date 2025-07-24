import click
import asyncio
import yaml
import re
import os
import getpass
import sys
from rich.console import Console
from rich.prompt import Prompt
from app.chat import Chat
from app.orchestrator import parallel_query, sequential_refinement, MODEL_CONFIG
from app.key_management import get_api_keys
from app.session import start_session, stop_session, get_password_from_session

console = Console()

# --- Configuration Loading & Saving ---
CONFIG_PATH = "config.yaml"

def load_config(file_path):
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"main_llm": {"provider": "gemini", "model": "gemini-1.5-flash-latest"}, "chains": {}}

def save_config(data, file_path):
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

CONFIG = load_config(CONFIG_PATH)
MAIN_LLM_CONFIG = CONFIG.get("main_llm")

# --- Main Application ---
@click.group(invoke_without_command=True)
@click.option('--no-mask', is_flag=True, help="Disable password masking for environments that don't support it.")
@click.pass_context
def cli(ctx, no_mask):
    """LLM Orchestrator CLI. Run without a command to start an interactive chat session."""
    ctx.obj = {'no_mask': no_mask}
    if ctx.invoked_subcommand is None:
        password = get_password(None, no_mask)
        try:
            chat_session = Chat(main_llm_config=MAIN_LLM_CONFIG, password=password)
            asyncio.run(chat_session.start())
        except (ValueError, FileNotFoundError) as e:
            console.print(f"[bold red]Error starting chat:[/bold red] {e}")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")

# --- 'run' Command ---
@cli.command()
@click.option('-p', '--prompt', required=True)
@click.option('--model', 'parallel_models', multiple=True, default=[])
@click.option('--step', 'steps', multiple=True, default=[])
@click.option('--password', 'password_option', help="Master password (optional).")
def run(prompt, parallel_models, steps, password_option):
    """Run a single-shot parallel or sequential query."""
    password = get_password(password_option)
    # ... (implementation is the same)

# --- 'chain' Command Group ---
@cli.group()
def chain():
    """Manage saved chains."""
    pass
# ... (chain subcommands are the same)
cli.add_command(chain)

# --- 'chat' Command Group ---
@cli.group()
def chat():
    """Manage chat sessions."""
    pass

@chat.command(name="list")
def list_chats():
    """List saved chat conversations."""
    if not os.path.exists("conversations"):
        console.print("[yellow]No conversations found.[/yellow]")
        return

    files = os.listdir("conversations")
    if not files:
        console.print("[yellow]No conversations found.[/yellow]")
        return

    console.print("[bold yellow]Saved conversations:[/bold yellow]")
    for f in sorted(files):
        console.print(f"  - {f}")

cli.add_command(chat)

# --- 'auth' Command Group ---
@cli.group()
def auth():
    """Manage authentication sessions."""
    pass
# ... (auth subcommands are the same)
cli.add_command(auth)

# --- 'config' Command Group ---
@cli.group()
def config():
    """Manage configuration settings."""
    pass

@config.command(name="set-main")
@click.argument('provider', type=click.Choice(list(MODEL_CONFIG.keys())))
@click.argument('model_name', type=click.STRING, required=False)
def set_main(provider, model_name):
    """
    Set the main LLM for interactive chat.

    If MODEL_NAME is not provided, the provider's default model will be used.
    """
    provider_config = MODEL_CONFIG.get(provider, {})
    
    if model_name is None:
        # Use the default model for the provider
        model_name = provider_config.get('default_model')
        if not model_name:
            console.print(f"[bold red]Error:[/bold red] No default model defined for provider '{provider}'.")
            return
        console.print(f"[italic]No model specified, using default for {provider}: {model_name}[/italic]")
    else:
        # Verify the specified model is valid for the provider
        available_models = [m['name'] for m in provider_config.get('models', [])]
        if model_name not in available_models:
            console.print(f"[bold red]Error:[/bold red] Model '{model_name}' not found for provider '{provider}'.")
            console.print(f"Available models: {', '.join(available_models)}")
            return

    CONFIG['main_llm'] = {'provider': provider, 'model': model_name}
    save_config(CONFIG, CONFIG_PATH)
    console.print(f"Main LLM set to: [bold green]{provider} ({model_name})[/bold green]")

cli.add_command(config)

# --- Utility Functions ---
import getpass

def get_password(password_option, no_mask=False):
    if password_option:
        return password_option
    cached_password = get_password_from_session()
    if cached_password:
        return cached_password
    if no_mask:
        print("Enter master password: ", end="", flush=True)
        return sys.stdin.readline().strip()
    try:
        return Prompt.ask("Enter master password", password=True)
    except (getpass.GetPassWarning, RuntimeError):
        console.print("[yellow]Warning: Password input may be echoed.[/yellow]")
        print("Enter master password: ", end="", flush=True)
        return sys.stdin.readline().strip()

def parse_step(step_str: str):
    match = re.match(r"^(?P<role>\w+)>/(?P<persona>\w+)\)-(?P<model>\w+)$", step_str)
    if not match:
        console.print(f"[bold red]Invalid step format:[/bold red] '{step_str}'.")
        return None
    return match.groupdict()

if __name__ == '__main__':
    cli()