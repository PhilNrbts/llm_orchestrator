from typing import Dict, Any, Optional
from rich.console import Console
from .loader import load_config
from .executor import WorkflowExecutor
from .workflow_models import Config

console = Console()

class WorkflowEngine:
    """
    Main workflow engine that coordinates configuration loading and workflow execution.
    """
    
    def __init__(self, config_path: str = "config.yaml", vault_password: str = None):
        """
        Initialize the workflow engine with configuration validation.
        
        Args:
            config_path: Path to the configuration file
            vault_password: Password for decrypting API keys (optional)
        """
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.executor = WorkflowExecutor(vault_password)
        
        # Load and validate configuration on initialization
        self._load_configuration()
    
    def _load_configuration(self):
        """Load and validate the configuration file."""
        self.config = load_config(self.config_path)
        console.print(f"📋 Loaded {len(self.config.workflows)} workflows: {list(self.config.workflows.keys())}")
    
    def list_workflows(self) -> Dict[str, Any]:
        """
        List all available workflows with their parameters.
        
        Returns:
            Dict mapping workflow names to their parameter definitions
        """
        if not self.config:
            return {}
        
        workflows_info = {}
        for name, workflow in self.config.workflows.items():
            # Extract parameter information
            if isinstance(workflow.params, list):
                params_info = []
                for param in workflow.params:
                    if isinstance(param, str):
                        params_info.append({"name": param, "required": True})
                    elif isinstance(param, dict):
                        for key, value in param.items():
                            if isinstance(value, str):
                                params_info.append({"name": key, "default": value, "required": False})
                            else:
                                params_info.append({"name": key, "required": value.get("required", True)})
            else:
                params_info = [
                    {"name": name, "required": param.required, "type": param.type, "description": param.description}
                    for name, param in workflow.params.items()
                ]
            
            workflows_info[name] = {
                "parameters": params_info,
                "steps": len(workflow.steps),
                "step_names": [step.name for step in workflow.steps]
            }
        
        return workflows_info
    
    def run(self, workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow with the given parameters.
        
        Args:
            workflow_name: Name of the workflow to execute
            params: Parameters to pass to the workflow
            
        Returns:
            Dict containing the workflow execution results
            
        Raises:
            ValueError: If the workflow doesn't exist
        """
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        
        if workflow_name not in self.config.workflows:
            available = list(self.config.workflows.keys())
            raise ValueError(f"Workflow '{workflow_name}' not found. Available workflows: {available}")
        
        workflow = self.config.workflows[workflow_name]
        
        console.print(f"\n📊 Workflow Info:")
        console.print(f"  • Name: {workflow_name}")
        console.print(f"  • Steps: {len(workflow.steps)}")
        console.print(f"  • Parameters: {list(params.keys())}")
        
        # Execute the workflow
        return self.executor.execute_workflow(workflow_name, workflow, params)
    
    def validate_workflow(self, workflow_name: str) -> bool:
        """
        Validate a specific workflow configuration.
        
        Args:
            workflow_name: Name of the workflow to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.config or workflow_name not in self.config.workflows:
            return False
        
        try:
            workflow = self.config.workflows[workflow_name]
            # Basic validation - check that all steps have required fields
            for step in workflow.steps:
                if not step.name or not step.tool:
                    return False
            return True
        except Exception:
            return False
    
    def reload_config(self):
        """Reload the configuration file."""
        console.print("🔄 Reloading configuration...")
        self._load_configuration()


def main():
    """Example usage of the workflow engine."""
    try:
        engine = WorkflowEngine()
        
        # List available workflows
        workflows = engine.list_workflows()
        console.print("\n📋 Available Workflows:")
        for name, info in workflows.items():
            console.print(f"  • {name}: {info['steps']} steps")
            for param in info['parameters']:
                required = "required" if param.get('required', True) else "optional"
                console.print(f"    - {param['name']} ({required})")
        
        # Example workflow execution
        if "sequential_elaboration" in workflows:
            console.print("\n🧪 Testing sequential_elaboration workflow...")
            result = engine.run("sequential_elaboration", {
                "user_prompt": "What are the key benefits of renewable energy?"
            })
            console.print(f"\n📊 Workflow Result: {result}")
        
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")


if __name__ == '__main__':
    main()
