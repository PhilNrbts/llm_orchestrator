import os
import json
import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from app.orchestrator import get_client, MODEL_CONFIG, get_system_prompts
from app.key_management import get_api_keys

console = Console()

class CommandCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lower()
        if text.startswith('/'):
            if ' ' not in text:
                for command in self.commands:
                    if command.startswith(text):
                        yield Completion(command, start_position=-len(text))

class Chat:
    """
    The main class for the interactive chat.

    Args:
        main_llm_config (dict): The main LLM configuration.
        password (str): The master password.
    """
    def __init__(self, main_llm_config: dict, password: str):
        self.api_keys = get_api_keys(password)
        self.provider = main_llm_config['provider']
        self.model_name = main_llm_config['model']
        self.history = []
        self.carry_context = False
        self.system_prompts = get_system_prompts()
        self.current_mode = "default"
        self.should_exit = False
        self._update_client()

        self.commands = {
            "/help": self._show_help,
            "/changeprovider": self._handle_change_provider,
            "/changemodel": self._handle_change_model,
            "/list": self._list_models,
            "/config": self._show_config,
            "/mode": self._handle_mode_change,
            "/exit": self._handle_exit,
            "/quit": self._handle_exit,
        }
        self.command_completer = CommandCompleter(list(self.commands.keys()))

    def _update_client(self):
        """Update the client based on the current provider and model."""
        provider_config = MODEL_CONFIG.get(self.provider)
        if not provider_config:
            raise ValueError(f"Provider '{self.provider}' not found in models.yaml")

        model_details_list = [m for m in provider_config['models'] if m['name'] == self.model_name]
        if not model_details_list:
            raise ValueError(f"Model '{self.model_name}' not found for provider '{self.provider}'")
        model_details = model_details_list[0]

        api_key_name = provider_config['api_key_name']
        api_key = self.api_keys.get(api_key_name)
        if not api_key:
            raise ValueError(f"API key '{api_key_name}' not found in vault.")

        model_config_for_client = model_details.copy()
        model_config_for_client['model'] = self.model_name

        self.client = get_client(
            client_name=self.provider,
            api_key=api_key,
            model_config=model_config_for_client
        )

    def _make_layout(self) -> Layout:
        """Create the layout for the chat UI."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=3, name="footer"),
        )
        layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
        return layout

    def _update_layout(self, layout: Layout):
        """Update the layout with the current chat state."""
        header_text = Text(f"LLM Orchestrator", justify="center", style="bold magenta")
        layout["header"].update(Panel(header_text))

        chat_history_text = Text()
        for item in self.history:
            chat_history_text.append(Text.from_markup(f"[bold cyan]{item['role']}:[/bold cyan] {item['content']}\n"))
        layout["body"].update(Panel(chat_history_text, title="Chat History"))

        sidebar_text = "[bold]Commands:[/bold]\n" + "\n".join(self.commands.keys())
        layout["side"].update(Panel(sidebar_text, title="Info"))

        footer_text = Text(f"Provider: {self.provider} | Model: {self.model_name} | Mode: {self.current_mode}", justify="right")
        layout["footer"].update(Panel(footer_text))
        return layout

    def _show_help(self):
        """Show available commands."""
        console.print("\n[bold yellow]Available commands:[/bold yellow]")
        for command, func in self.commands.items():
            console.print(f"  [bold]{command}[/bold] - {func.__doc__}")

    def _handle_exit(self):
        """Exit the chat."""
        self.should_exit = True

    def _handle_change_provider(self):
        """Change the provider."""
        console.print("\n[bold yellow]Available providers:[/bold yellow]")
        providers = list(MODEL_CONFIG.keys())
        for i, p in enumerate(providers, 1):
            console.print(f"  [{i}] {p}")
        
        choice_str = Prompt.ask("Choose a provider", choices=[str(i) for i in range(1, len(providers) + 1)])
        new_provider = providers[int(choice_str) - 1]

        if new_provider == self.provider:
            console.print(f"[italic]You are already using {new_provider}.[/italic]")
            return

        self.provider = new_provider
        self.model_name = MODEL_CONFIG[new_provider]['default_model']
        self._ask_for_context()
        self._update_client()

    def _handle_change_model(self):
        """Change the model."""
        console.print(f"\n[bold yellow]Available models for {self.provider}:[/bold yellow]")
        models = [m['name'] for m in MODEL_CONFIG[self.provider]['models']]
        for i, m in enumerate(models, 1):
            console.print(f"  [{i}] {m}")

        choice_str = Prompt.ask("Choose a model", choices=[str(i) for i in range(1, len(models) + 1)])
        new_model = models[int(choice_str) - 1]

        if new_model == self.model_name:
            console.print(f"[italic]You are already using {new_model}.[/italic]")
            return
            
        self.model_name = new_model
        self._ask_for_context()
        self._update_client()

    def _list_models(self):
        """List available models for the current provider."""
        console.print(f"\n[bold yellow]Available models for {self.provider}:[/bold yellow]")
        models = [m['name'] for m in MODEL_CONFIG[self.provider]['models']]
        for model in models:
            console.print(f"  - {model}")

    def _show_config(self):
        """Show the current configuration."""
        console.print("\n[bold yellow]Current Configuration:[/bold yellow]")
        console.print(f"  - Provider: {self.provider}")
        console.print(f"  - Model: {self.model_name}")
        console.print(f"  - Mode: {self.current_mode}")

    def _handle_mode_change(self):
        """Change the chat mode."""
        console.print("\n[bold yellow]Available modes:[/bold yellow]")
        modes = ["default"] + self.system_prompts.get('personas', [])
        for i, mode in enumerate(modes, 1):
            console.print(f"  [{i}] {mode}")

        choice_str = Prompt.ask("Choose a mode", choices=[str(i) for i in range(1, len(modes) + 1)])
        self.current_mode = modes[int(choice_str) - 1]
        console.print(f"Mode changed to: [bold green]{self.current_mode}[/bold green]")
        self._update_client()

    def _ask_for_context(self):
        """Ask the user if they want to provide the conversation history as context."""
        if self.history:
            self.carry_context = Prompt.ask(
                f"Provide conversation history as context? (y/n)",
                choices=["y", "n"], default="y"
            ) == "y"

    def _prepare_prompt(self, prompt: str) -> str:
        """
        Prepare the prompt by optionally prepending the conversation history and system prompt.

        Args:
            prompt (str): The user's prompt.

        Returns:
            str: The prepared prompt.
        """
        final_prompt = prompt
        if self.current_mode != "default":
            system_prompt = self.system_prompts.get('personas', {}).get(self.current_mode, "")
            if system_prompt:
                final_prompt = f"{system_prompt}\n\n{prompt}"

        if not self.carry_context or not self.history:
            return final_prompt
        
        context = "\n".join([f"{item['role']}: {item['content']}" for item in self.history])
        self.carry_context = False
        return f"--- Conversation History ---\n{context}\n--- New Prompt ---\n{final_prompt}"

    from prompt_toolkit.filters import Condition

    async def start(self):
        """Start the interactive chat session."""
        layout = self._make_layout()
        
        bindings = KeyBindings()
        @bindings.add('down', filter=Condition(lambda: not get_app().current_buffer.text))
        def _(event):
            event.app.current_buffer.start_completion(select_first=False)

        session = PromptSession(completer=self.command_completer, complete_while_typing=True, key_bindings=bindings)
        try:
            while not self.should_exit:
                console.clear()
                console.print(self._update_layout(layout))
                prompt = await session.prompt_async("\n> ")

                if prompt.lower() in ["exit", "quit"]:
                    break
                
                if prompt.startswith("/"):
                    command_text = prompt.lower()
                    command = self.commands.get(command_text)
                    if command:
                        command()
                        if not self.should_exit:
                            await session.prompt_async("Press Enter to continue...")
                    else:
                        console.print("[bold red]Unknown command. Type /help for a list of commands.[/bold red]")
                        await session.prompt_async("Press Enter to continue...")
                    continue

                final_prompt = self._prepare_prompt(prompt)
                self.history.append({"role": "user", "content": prompt})
                
                with console.status("[italic]Waiting for response...[/italic]"):
                    response = await self.client.query(final_prompt)
                
                self.history.append({"role": f"{self.provider}/{self.model_name}", "content": response})
        finally:
            self.save_conversation()

    def save_conversation(self):
        """Save the conversation to a timestamped file."""
        if not self.history:
            return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("conversations", exist_ok=True)
        filename = f"conversations/chat_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(self.history, f, indent=2)
        console.print(f"\n[italic]Conversation saved to {filename}[/italic]")