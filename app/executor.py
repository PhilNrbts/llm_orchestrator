import re
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from .workflow_models import Workflow, Step
from .loader import validate_workflow_params
from .tools.model_call import ModelCallTool
from .tools.parallel_query import ParallelQueryTool

console = Console()


class WorkflowExecutor:
    """
    Core workflow execution engine that processes steps and resolves dynamic inputs.
    """

    def __init__(self, vault_password: Optional[str] = None, memory_manager=None):
        self.step_outputs: Dict[str, Any] = {}
        self.current_params: Dict[str, Any] = {}
        self.vault_password = vault_password
        self.memory_manager = memory_manager

        # Initialize tool registry
        self.tools = {
            "model_call": ModelCallTool(vault_password),
            "parallel_query": ParallelQueryTool(vault_password),
        }

    def execute_workflow(
        self, workflow_name: str, workflow: Workflow, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow with the given parameters.

        Args:
            workflow_name: Name of the workflow being executed
            workflow: Validated workflow object
            params: Parameters provided for the workflow

        Returns:
            Dict containing the outputs of all executed steps
        """
        console.print(f"\n🚀 Starting workflow: [bold blue]{workflow_name}[/bold blue]")

        # Initialize memory for this workflow execution
        if self.memory_manager:
            workflow_id = self.memory_manager.start_workflow(workflow_name, params)
            console.print(f"🧠 Memory initialized: {workflow_id}")

        # Validate and process parameters
        try:
            # Convert workflow.params to dict format for validation
            workflow_params_dict = {}
            if isinstance(workflow.params, list):
                # Handle list format from config.yaml
                for param in workflow.params:
                    if isinstance(param, str):
                        workflow_params_dict[param] = {"required": True}
                    elif isinstance(param, dict):
                        workflow_params_dict.update(param)
            else:
                # Handle Param objects
                workflow_params_dict = {
                    name: param.dict() for name, param in workflow.params.items()
                }

            self.current_params = validate_workflow_params(
                workflow_name, {"params": workflow.params}, params
            )
            console.print(f"✅ Parameters validated: {list(self.current_params.keys())}")

        except ValueError as e:
            console.print(f"❌ Parameter validation failed: {str(e)}", style="red")
            return {"error": str(e)}

        # Reset step outputs for this workflow execution
        self.step_outputs = {}

        # Execute each step in sequence
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            for i, step in enumerate(workflow.steps, 1):
                task = progress.add_task(
                    f"Executing step {i}/{len(workflow.steps)}: {step.name}", total=None
                )

                try:
                    # Check if this is a scrutiny gate
                    if step.gate:
                        gate_result = self._handle_scrutiny_gate(step)
                        if not gate_result:
                            console.print(
                                f"🛑 Workflow stopped at gate: {step.name}",
                                style="yellow",
                            )
                            break
                        continue

                    # Fetch memory context for this step FIRST
                    memory_context = {}
                    if self.memory_manager:
                        # Convert step to dict format for memory manager
                        step_config = {
                            "name": step.name,
                            "tool": step.tool,
                            "inputs": step.inputs,
                            "memory": getattr(step, "memory", {}),
                        }
                        memory_context = self.memory_manager.fetch_context_for_step(
                            step_config
                        )
                        if memory_context:
                            console.print(
                                f"🧠 Memory context loaded: {list(memory_context.keys())}"
                            )

                    # Inject memory context into inputs BEFORE resolving templates
                    inputs_with_memory = step.inputs
                    if self.memory_manager and memory_context:
                        inputs_with_memory = self.memory_manager.inject_memory_context(
                            step.inputs, memory_context
                        )

                    # Now resolve dynamic inputs (including memory-injected ones)
                    resolved_inputs = self._resolve_inputs(
                        inputs_with_memory, self.current_params, self.step_outputs
                    )

                    # Execute the step
                    step_output = self._execute_step(step, resolved_inputs)

                    # Save step result to memory
                    if self.memory_manager:
                        self.memory_manager.save_step_result(step.name, step_output)

                    # Store the output for future steps
                    self.step_outputs[step.name] = step_output

                    progress.update(task, completed=True)
                    console.print(f"✅ Step '{step.name}' completed", style="green")

                except Exception as e:
                    progress.update(task, completed=True)
                    console.print(f"❌ Step '{step.name}' failed: {str(e)}", style="red")

                    # Handle failure based on step configuration
                    if step.on_failure == "abort_chain":
                        console.print(
                            "🛑 Aborting workflow due to step failure", style="red"
                        )
                        return {
                            "error": f"Step '{step.name}' failed: {str(e)}",
                            "completed_steps": self.step_outputs,
                        }
                    elif step.on_failure == "continue":
                        console.print(
                            "⚠️  Continuing workflow despite step failure",
                            style="yellow",
                        )
                        self.step_outputs[step.name] = {"error": str(e)}
                        continue

        console.print(
            f"🎉 Workflow '{workflow_name}' completed successfully!", style="bold green"
        )
        return self.step_outputs

    def _resolve_inputs(
        self,
        step_inputs: Dict[str, Any],
        params: Dict[str, Any],
        previous_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve dynamic inputs using {{...}} syntax.

        Args:
            step_inputs: Raw inputs from the step definition
            params: Workflow parameters
            previous_outputs: Outputs from previous steps

        Returns:
            Dict with resolved input values
        """
        resolved = {}

        for key, value in step_inputs.items():
            if isinstance(value, str):
                resolved[key] = self._resolve_template_string(
                    value, params, previous_outputs
                )
            elif isinstance(value, dict):
                resolved[key] = self._resolve_inputs(value, params, previous_outputs)
            elif isinstance(value, list):
                resolved[key] = [
                    self._resolve_template_string(item, params, previous_outputs)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                resolved[key] = value

        return resolved

    def _resolve_template_string(
        self, template: str, params: Dict[str, Any], previous_outputs: Dict[str, Any]
    ) -> str:
        """
        Resolve a single template string with {{...}} placeholders.

        Args:
            template: String potentially containing {{...}} placeholders
            params: Workflow parameters
            previous_outputs: Outputs from previous steps

        Returns:
            String with placeholders resolved
        """
        # Find all {{...}} patterns
        pattern = r"\{\{([^}]+)\}\}"
        matches = re.findall(pattern, template)

        resolved_template = template

        for match in matches:
            placeholder = f"{{{{{match}}}}}"
            value = self._lookup_value(match.strip(), params, previous_outputs)
            resolved_template = resolved_template.replace(placeholder, str(value))

        return resolved_template

    def _lookup_value(
        self, path: str, params: Dict[str, Any], previous_outputs: Dict[str, Any]
    ) -> Any:
        """
        Look up a value from params, previous step outputs, or memory context.

        Args:
            path: Dot-notation path like 'params.query', 'steps.initial_answer.output', or 'memory.user_prompt'
            params: Workflow parameters
            previous_outputs: Outputs from previous steps

        Returns:
            The resolved value

        Raises:
            KeyError: If the path cannot be resolved
        """
        parts = path.split(".")

        if parts[0] == "params":
            # Look up in parameters
            if len(parts) == 2:
                if parts[1] in params:
                    return params[parts[1]]
                else:
                    raise KeyError(f"Parameter '{parts[1]}' not found")
            else:
                raise KeyError(f"Invalid parameter path: {path}")

        elif parts[0] == "steps":
            # Look up in previous step outputs
            if len(parts) >= 2:
                step_name = parts[1]
                if step_name not in previous_outputs:
                    raise KeyError(f"Step '{step_name}' output not found")

                result = previous_outputs[step_name]

                # Navigate deeper into the output if needed
                for part in parts[2:]:
                    if isinstance(result, dict) and part in result:
                        result = result[part]
                    else:
                        # If no specific field is found, return the whole output
                        # This handles cases where steps.step_name.output is expected
                        # but the step just returns a string directly
                        if part == "output" and isinstance(
                            result, (str, int, float, bool)
                        ):
                            return result
                        raise KeyError(f"Path '{path}' not found in step output")

                return result
            else:
                raise KeyError(f"Invalid step path: {path}")

        elif parts[0] == "memory":
            # Memory context should already be resolved by memory manager
            # If we get here, it means the memory injection didn't work properly
            # Return a placeholder to indicate the issue
            return f"[Memory context not resolved: {path}]"

        else:
            raise KeyError(
                f"Unknown path prefix: {parts[0]}. Use 'params.', 'steps.', or 'memory.'"
            )

    def _execute_step(
        self, step: Step, resolved_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single step using the real tool implementations.

        Args:
            step: Step configuration
            resolved_inputs: Inputs with resolved placeholders

        Returns:
            Dict containing the step output
        """
        console.print(
            Panel(
                f"[bold]Tool:[/bold] {step.tool}\n"
                f"[bold]Inputs:[/bold]\n"
                + "\n".join([f"  • {k}: {v}" for k, v in resolved_inputs.items()]),
                title=f"Executing: {step.name}",
                border_style="blue",
            )
        )

        # Check if we have a registered tool for this step
        if step.tool in self.tools:
            tool_instance = self.tools[step.tool]
            try:
                # Execute the real tool
                step_result = tool_instance.execute(**resolved_inputs)
                return step_result
            except Exception as e:
                console.print(f"❌ Tool execution failed: {str(e)}", style="red")
                raise e
        else:
            # Fallback for unknown tools
            console.print(
                f"⚠️  Unknown tool '{step.tool}', using simulation", style="yellow"
            )
            return {
                "output": f"[Simulated output from unknown tool: {step.tool}]",
                "inputs": resolved_inputs,
            }

    def _handle_scrutiny_gate(self, step: Step) -> bool:
        """
        Handle a scrutiny gate step by prompting the user for approval.

        Args:
            step: Step with gate configuration

        Returns:
            bool: True if approved, False if rejected
        """
        gate_config = step.gate
        prompt_text = gate_config.get("prompt", f"Approve step '{step.name}'?")

        # Resolve any placeholders in the gate prompt
        resolved_prompt = self._resolve_template_string(
            prompt_text, self.current_params, self.step_outputs
        )

        console.print(
            Panel(
                resolved_prompt,
                title=f"🚪 Scrutiny Gate: {step.name}",
                border_style="yellow",
            )
        )

        while True:
            response = (
                console.input("\n[bold yellow]Approve (y/n)?[/bold yellow] ")
                .lower()
                .strip()
            )
            if response in ["y", "yes"]:
                console.print("✅ Gate approved, continuing workflow", style="green")
                return True
            elif response in ["n", "no"]:
                console.print("❌ Gate rejected, stopping workflow", style="red")
                return False
            else:
                console.print("Please enter 'y' or 'n'", style="yellow")
