import asyncio
import getpass
import os
import re
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from app.chat import Chat
from app.orchestrator import MODEL_CONFIG
from app.session import get_password_from_session
from app.workflow_engine import WorkflowEngine
from app.memory_store import MemoryStore

console = Console()

# --- Configuration Loading & Saving ---
def get_config_path():
    """Get the path to the config file, creating the directory if needed."""
    config_dir = Path(os.path.expanduser("~")) / ".config" / "gemini-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.yaml"

CONFIG_PATH = get_config_path()


def load_config(file_path):
    """
    Load the configuration from a YAML file.

    Args:
        file_path (str): The path to the configuration file.

    Returns:
        dict: The configuration dictionary.
    """
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "main_llm": {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
            "chains": {},
        }


def save_config(data, file_path):
    """
    Save the configuration to a YAML file.

    Args:
        data (dict): The configuration dictionary to save.
        file_path (str): The path to the configuration file.
    """
    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


CONFIG = load_config(CONFIG_PATH)
MAIN_LLM_CONFIG = CONFIG.get("main_llm")


# --- Main Application ---
@click.group(invoke_without_command=True)
@click.option(
    "--no-mask",
    is_flag=True,
    help="Disable password masking for environments that don't support it.",
)
@click.pass_context
def cli(ctx, no_mask):
    """LLM Orchestrator CLI. Run without a command to start an interactive chat session."""
    ctx.obj = {"no_mask": no_mask}
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
@click.option("-p", "--prompt", required=True)
@click.option("--model", "parallel_models", multiple=True, default=[])
@click.option("--step", "steps", multiple=True, default=[])
@click.option("--password", "password_option", help="Master password (optional).")
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
@click.argument("provider", type=click.Choice(list(MODEL_CONFIG.keys())))
@click.argument("model_name", type=click.STRING, required=False)
def set_main(provider, model_name):
    """
    Set the main LLM for interactive chat.

    If MODEL_NAME is not provided, the provider's default model will be used.
    """
    provider_config = MODEL_CONFIG.get(provider, {})

    if model_name is None:
        # Use the default model for the provider
        model_name = provider_config.get("default_model")
        if not model_name:
            console.print(
                f"[bold red]Error:[/bold red] No default model defined for provider '{provider}'."
            )
            return
        console.print(
            f"[italic]No model specified, using default for {provider}: {model_name}[/italic]"
        )
    else:
        # Verify the specified model is valid for the provider
        available_models = [m["name"] for m in provider_config.get("models", [])]
        if model_name not in available_models:
            console.print(
                f"[bold red]Error:[/bold red] Model '{model_name}' not found for provider '{provider}'."
            )
            console.print(f"Available models: {', '.join(available_models)}")
            return

    CONFIG["main_llm"] = {"provider": provider, "model": model_name}
    save_config(CONFIG, CONFIG_PATH)
    console.print(
        f"Main LLM set to: [bold green]{provider} ({model_name})[/bold green]"
    )


cli.add_command(config)


# --- 'workflow' Command Group ---
@cli.group()
def workflow():
    """Manage and execute intelligent workflows with memory."""
    pass


@workflow.command(name="list")
def list_workflows():
    """List all available workflows from config.yaml."""
    try:
        engine = WorkflowEngine()
        workflows = engine.list_workflows()
        
        if not workflows:
            console.print("[yellow]No workflows found in config.yaml[/yellow]")
            return
        
        console.print(Panel.fit(
            "[bold blue]Available Workflows[/bold blue]",
            border_style="blue"
        ))
        
        for name, info in workflows.items():
            # Create a table for each workflow
            table = Table(title=f"🔧 {name}", show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            
            table.add_row("Steps", str(info['steps']))
            table.add_row("Step Names", ", ".join(info['step_names']))
            
            # Add parameters information
            if info['parameters']:
                param_list = []
                for param in info['parameters']:
                    param_name = param['name']
                    required = param.get('required', True)
                    default = param.get('default')
                    param_type = param.get('type', 'str')
                    
                    param_str = f"{param_name} ({param_type})"
                    if not required:
                        param_str += " [optional]"
                    if default:
                        param_str += f" = {default}"
                    param_list.append(param_str)
                
                table.add_row("Parameters", "\n".join(param_list))
            else:
                table.add_row("Parameters", "None")
            
            console.print(table)
            console.print()  # Add spacing between workflows
            
    except Exception as e:
        console.print(f"[bold red]Error loading workflows:[/bold red] {e}")


@workflow.command(name="run")
@click.argument("workflow_name")
@click.option("--param", "params", multiple=True, 
              help='Workflow parameters in format key=value (e.g., --param "user_prompt=Explain AI")')
@click.option("--password", "password_option", help="Master password (optional).")
def run_workflow(workflow_name, params, password_option):
    """Execute a workflow with specified parameters."""
    password = get_password(password_option)
    
    try:
        # Parse parameters from command line
        parsed_params = {}
        for param in params:
            if "=" not in param:
                console.print(f"[bold red]Error:[/bold red] Invalid parameter format '{param}'. Use key=value format.")
                return
            key, value = param.split("=", 1)
            parsed_params[key.strip()] = value.strip()
        
        console.print(Panel.fit(
            f"[bold green]Executing Workflow: {workflow_name}[/bold green]",
            border_style="green"
        ))
        
        # Initialize workflow engine with password
        engine = WorkflowEngine(vault_password=password)
        
        # Validate workflow exists
        workflows = engine.list_workflows()
        if workflow_name not in workflows:
            console.print(f"[bold red]Error:[/bold red] Workflow '{workflow_name}' not found.")
            console.print(f"Available workflows: {', '.join(workflows.keys())}")
            return
        
        # Check if all required parameters are provided
        workflow_info = workflows[workflow_name]
        required_params = [p['name'] for p in workflow_info['parameters'] if p.get('required', True)]
        missing_params = [p for p in required_params if p not in parsed_params]
        
        if missing_params:
            console.print(f"[bold red]Error:[/bold red] Missing required parameters: {', '.join(missing_params)}")
            console.print("\nRequired parameters:")
            for param in workflow_info['parameters']:
                if param.get('required', True):
                    param_type = param.get('type', 'str')
                    console.print(f"  --param \"{param['name']}=<{param_type}>\"")
            return
        
        # Execute the workflow
        console.print(f"\n🚀 Starting workflow execution...")
        console.print(f"📋 Parameters: {parsed_params}")
        console.print()
        
        result = engine.run(workflow_name, parsed_params)
        
        # Display results
        console.print(Panel.fit(
            "[bold green]✅ Workflow Completed Successfully![/bold green]",
            border_style="green"
        ))
        
        # Create results table
        results_table = Table(title="📊 Execution Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Step", style="yellow", no_wrap=True)
        results_table.add_column("Output", style="white")
        results_table.add_column("Provider", style="magenta", no_wrap=True)
        results_table.add_column("Model", style="blue", no_wrap=True)
        
        for step_name, step_result in result.items():
            if isinstance(step_result, dict):
                output = step_result.get('output', 'N/A')
                provider = step_result.get('provider', 'Unknown')
                model = step_result.get('model', 'Unknown')
                
                # Truncate long outputs for display
                if len(output) > 100:
                    output = output[:97] + "..."
                
                results_table.add_row(step_name, output, provider, model)
        
        console.print(results_table)
        
        # Show memory information
        if os.path.exists("memory.db"):
            console.print(f"\n💾 Memory entries have been saved to memory.db")
            console.print(f"🔍 Use 'llm-cli workflow inspect' to view detailed execution history")
        
    except ValueError as e:
        console.print(f"[bold red]Workflow Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]Execution Error:[/bold red] {e}")


@workflow.command(name="inspect")
@click.argument("run_id", required=False)
@click.option("--recent", is_flag=True, help="Show the most recent workflow run.")
@click.option("--all", is_flag=True, help="Show all workflow runs.")
def inspect_workflow(run_id, recent, all):
    """Inspect workflow execution results and memory entries."""
    try:
        if not os.path.exists("memory.db"):
            console.print("[yellow]No memory database found. Run a workflow first.[/yellow]")
            return
        
        memory_store = MemoryStore("memory.db")
        
        if all:
            # Show statistics about all workflows
            stats = memory_store.get_stats()
            
            console.print(Panel.fit(
                "[bold blue]📊 Workflow Memory Statistics[/bold blue]",
                border_style="blue"
            ))
            
            stats_table = Table(show_header=False)
            stats_table.add_column("Metric", style="cyan", no_wrap=True)
            stats_table.add_column("Value", style="white")
            
            stats_table.add_row("Total Memory Entries", str(stats['total_entries']))
            stats_table.add_row("Unique Workflows", str(stats['unique_workflows']))
            stats_table.add_row("Database Size", f"{stats['database_size_bytes']} bytes")
            
            for classification, count in stats['by_classification'].items():
                stats_table.add_row(f"  └─ {classification.title()}", str(count))
            
            console.print(stats_table)
            return
        
        # Get workflow runs from memory
        with sqlite3.connect("memory.db") as conn:
            cursor = conn.cursor()
            
            if recent or not run_id:
                # Show most recent workflow
                cursor.execute("""
                    SELECT workflow_id, MIN(timestamp) as start_time, MAX(timestamp) as end_time,
                           COUNT(*) as memory_entries
                    FROM memory_slices
                    GROUP BY workflow_id
                    ORDER BY start_time DESC
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if not result:
                    console.print("[yellow]No workflow runs found in memory database.[/yellow]")
                    return
                
                workflow_id, start_time, end_time, entry_count = result
                
            else:
                # Look for specific run_id
                cursor.execute("""
                    SELECT workflow_id, MIN(timestamp) as start_time, MAX(timestamp) as end_time,
                           COUNT(*) as memory_entries
                    FROM memory_slices
                    WHERE workflow_id LIKE ?
                    GROUP BY workflow_id
                    ORDER BY start_time DESC
                """, (f"%{run_id}%",))
                
                results = cursor.fetchall()
                if not results:
                    console.print(f"[yellow]No workflow run found matching '{run_id}'.[/yellow]")
                    return
                
                if len(results) > 1:
                    console.print(f"[yellow]Multiple workflows found matching '{run_id}':[/yellow]")
                    for i, (wid, start, end, count) in enumerate(results):
                        console.print(f"  {i+1}. {wid[-12:]}... ({start})")
                    return
                
                workflow_id, start_time, end_time, entry_count = results[0]
            
            # Display workflow execution details
            console.print(Panel.fit(
                f"[bold green]🔍 Workflow Execution Details[/bold green]",
                border_style="green"
            ))
            
            info_table = Table(show_header=False)
            info_table.add_column("Property", style="cyan", no_wrap=True)
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Workflow ID", workflow_id[-20:] + "..." if len(workflow_id) > 20 else workflow_id)
            info_table.add_row("Start Time", start_time)
            info_table.add_row("End Time", end_time)
            info_table.add_row("Memory Entries", str(entry_count))
            
            console.print(info_table)
            
            # Get detailed memory entries
            memory_entries = memory_store.retrieve(workflow_id=workflow_id, order_by="timestamp ASC")
            
            if memory_entries:
                console.print("\n📋 Memory Entries:")
                
                entries_table = Table(show_header=True, header_style="bold yellow")
                entries_table.add_column("Step", style="cyan", no_wrap=True)
                entries_table.add_column("Type", style="magenta", no_wrap=True)
                entries_table.add_column("Content Preview", style="white")
                entries_table.add_column("Timestamp", style="blue", no_wrap=True)
                
                for entry in memory_entries:
                    content = entry['content']
                    if len(content) > 80:
                        content = content[:77] + "..."
                    
                    timestamp = entry['timestamp'].split('T')[1][:8] if 'T' in entry['timestamp'] else entry['timestamp']
                    
                    entries_table.add_row(
                        entry['step_name'],
                        entry['classification'],
                        content,
                        timestamp
                    )
                
                console.print(entries_table)
            
    except Exception as e:
        console.print(f"[bold red]Error inspecting workflow:[/bold red] {e}")


cli.add_command(workflow)


# --- Utility Functions ---
import getpass


def get_password(password_option, no_mask=False):
    """
    Get the master password from the user.

    Args:
        password_option (str): The password provided as a command-line option.
        no_mask (bool): Whether to disable password masking.

    Returns:
        str: The master password.
    """
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
    """
    Parse a step string into a dictionary.

    Args:
        step_str (str): The step string to parse.

    Returns:
        dict: The parsed step dictionary.
    """
    match = re.match(r"^(?P<role>\w+)>/(?P<persona>\w+)\)-(?P<model>\w+)$", step_str)
    if not match:
        console.print(f"[bold red]Invalid step format:[/bold red] '{step_str}'.")
        return None
    return match.groupdict()


if __name__ == "__main__":
    cli()
