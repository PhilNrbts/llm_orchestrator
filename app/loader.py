import yaml
from pydantic import ValidationError
from typing import Dict, Any
from rich.console import Console
from .workflow_models import Config

console = Console()


def load_config(path: str = "config.yaml") -> Config:
    """
    Load and validate configuration from YAML file.

    Args:
        path: Path to the configuration file

    Returns:
        Config: Validated configuration object

    Raises:
        SystemExit: If configuration file is not found or invalid
    """
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Validate the configuration using Pydantic
        config = Config.model_validate(data)
        console.print(f"✅ Configuration loaded successfully from {path}", style="green")
        return config

    except FileNotFoundError:
        console.print(f"❌ Error: Configuration file not found at {path}", style="red")
        console.print(
            "Please ensure config.yaml exists in the current directory.", style="yellow"
        )
        raise SystemExit(1)

    except yaml.YAMLError as e:
        console.print(f"❌ Error: Invalid YAML syntax in {path}:", style="red")
        console.print(str(e), style="red")
        raise SystemExit(1)

    except ValidationError as e:
        console.print(f"❌ Error: Invalid configuration in {path}:", style="red")
        console.print(
            "Configuration validation failed with the following errors:", style="yellow"
        )

        # Format validation errors in a user-friendly way
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            console.print(f"  • {location}: {error['msg']}", style="red")
            if "input" in error:
                console.print(f"    Got: {error['input']}", style="dim red")

        console.print("\nPlease fix these errors and try again.", style="yellow")
        raise SystemExit(1)

    except Exception as e:
        console.print(
            f"❌ Unexpected error loading configuration: {str(e)}", style="red"
        )
        raise SystemExit(1)


def validate_workflow_params(
    workflow_name: str, workflow_config: Dict[str, Any], provided_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that all required workflow parameters are provided.

    Args:
        workflow_name: Name of the workflow
        workflow_config: Workflow configuration from config.yaml
        provided_params: Parameters provided by the user

    Returns:
        Dict[str, Any]: Validated and processed parameters

    Raises:
        ValueError: If required parameters are missing
    """
    # Handle both list and dict format for params
    workflow_params = workflow_config.get("params", [])

    if isinstance(workflow_params, list):
        # Convert list format to dict format for processing
        required_params = []
        optional_params = {}

        for param in workflow_params:
            if isinstance(param, str):
                required_params.append(param)
            elif isinstance(param, dict):
                for key, value in param.items():
                    if isinstance(value, str):
                        # Simple default value
                        optional_params[key] = value
                    else:
                        # Complex parameter definition
                        if value.get("required", True):
                            required_params.append(key)
                        else:
                            optional_params[key] = value.get("default")
    else:
        # Dict format (Param objects)
        required_params = [
            name for name, param in workflow_params.items() if param.required
        ]
        optional_params = {
            name: param.default
            for name, param in workflow_params.items()
            if not param.required
        }

    # Check for missing required parameters
    missing_params = [
        param for param in required_params if param not in provided_params
    ]
    if missing_params:
        raise ValueError(
            f"Missing required parameters for workflow '{workflow_name}': {missing_params}"
        )

    # Merge provided params with defaults
    final_params = {**optional_params, **provided_params}

    return final_params
