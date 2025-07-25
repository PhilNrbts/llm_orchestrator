# Custom Tool Development Tutorial

This tutorial walks you through creating a custom tool for the LLM Orchestrator, from implementation to integration in workflows.

## Overview

The LLM Orchestrator uses a plugin-based tool architecture where each tool inherits from `BaseTool` and implements the required interface. Tools can perform any operation - from calling external APIs to processing data to interacting with databases.

## Step 1: Understanding the BaseTool Interface

All tools must inherit from `app.tools.base.BaseTool` and implement the `execute` method:

```python
from app.tools.base import BaseTool
from typing import Dict, Any

class MyCustomTool(BaseTool):
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Your tool logic here
        return {
            "output": "Your tool's result",
            "metadata": {"any": "additional_info"}
        }
```

## Step 2: Create Your First Custom Tool

Let's create a simple "Weather Tool" that simulates fetching weather data.

### 2.1: Create the Tool File

Create a new file: `app/tools/weather.py`

```python
"""
Weather tool for demonstrating custom tool development.
This is a simplified example that simulates weather API calls.
"""

import random
from typing import Dict, Any
from app.tools.base import BaseTool


class WeatherTool(BaseTool):
    """
    A simple weather tool that simulates fetching weather data.
    
    Required inputs:
    - location: The location to get weather for (string)
    
    Optional inputs:
    - units: Temperature units ('celsius' or 'fahrenheit', default: 'celsius')
    """
    
    def validate_inputs(self, **kwargs) -> None:
        """Validate that required inputs are provided."""
        if 'location' not in kwargs:
            raise ValueError("Weather tool requires 'location' parameter")
        
        if not isinstance(kwargs['location'], str):
            raise ValueError("Location must be a string")
        
        # Validate optional units parameter
        units = kwargs.get('units', 'celsius')
        if units not in ['celsius', 'fahrenheit']:
            raise ValueError("Units must be 'celsius' or 'fahrenheit'")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the weather tool.
        
        Args:
            location: Location to get weather for
            units: Temperature units (optional)
            
        Returns:
            Dict containing weather information
        """
        # Validate inputs first
        self.validate_inputs(**kwargs)
        
        location = kwargs['location']
        units = kwargs.get('units', 'celsius')
        
        # Simulate API call with random weather data
        conditions = ['sunny', 'cloudy', 'rainy', 'partly cloudy', 'windy']
        condition = random.choice(conditions)
        
        # Generate temperature based on units
        if units == 'celsius':
            temperature = random.randint(-10, 35)
            temp_symbol = '°C'
        else:
            temperature = random.randint(14, 95)
            temp_symbol = '°F'
        
        # Create weather report
        weather_report = f"Weather in {location}: {condition}, {temperature}{temp_symbol}"
        
        return {
            "output": weather_report,
            "provider": "weather-api-simulator",
            "model": "v1.0",
            "simulated": True,
            "metadata": {
                "location": location,
                "condition": condition,
                "temperature": temperature,
                "units": units,
                "raw_data": {
                    "condition": condition,
                    "temp": temperature,
                    "units": units
                }
            }
        }
```

### 2.2: Register the Tool

Tools are automatically discovered by the tool registry. Add your tool to `app/tools/__init__.py`:

```python
"""
Tool registry for the LLM orchestrator.
"""

from .base import BaseTool
from .model_call import ModelCallTool
from .parallel_query import ParallelQueryTool
from .weather import WeatherTool  # Add your new tool

# Tool registry - maps tool names to tool classes
TOOL_REGISTRY = {
    "model_call": ModelCallTool,
    "parallel_query": ParallelQueryTool,
    "weather": WeatherTool,  # Register your tool
}

def get_tool(tool_name: str) -> BaseTool:
    """
    Get a tool instance by name.
    
    Args:
        tool_name: Name of the tool to get
        
    Returns:
        Tool instance
        
    Raises:
        ValueError: If tool is not found
    """
    if tool_name not in TOOL_REGISTRY:
        available_tools = list(TOOL_REGISTRY.keys())
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class()
```

## Step 3: Add Your Tool to a Workflow

Now you can use your tool in `config.yaml`:

```yaml
workflows:
  weather_report:
    params:
      - location
      - units  # optional parameter
    
    steps:
      - name: get_weather
        tool: weather
        inputs:
          location: "{{params.location}}"
          units: "{{params.units}}"
      
      - name: generate_summary
        tool: model_call
        inputs:
          prompt: "Based on this weather data: '{{get_weather.output}}', write a friendly weather summary for travelers."
          provider: "gemini"
          model: "gemini-1.5-flash"
        memory:
          needs: ["tool_output(get_weather)"]

  weather_with_advice:
    params:
      - location
    
    steps:
      - name: get_current_weather
        tool: weather
        inputs:
          location: "{{params.location}}"
          units: "celsius"
      
      - name: generate_advice
        tool: model_call
        inputs:
          prompt: |
            Weather: {{memory.get_current_weather_output}}
            
            Provide clothing and activity recommendations based on this weather.
        memory:
          needs: ["tool_output(get_current_weather)"]
```

## Step 4: Test Your Tool

### 4.1: Test Tool Directly

Create a test script `test_weather_tool.py`:

```python
#!/usr/bin/env python3
"""Test the weather tool directly."""

from app.tools.weather import WeatherTool

def test_weather_tool():
    tool = WeatherTool()
    
    # Test basic functionality
    result = tool.execute(location="San Francisco")
    print(f"Weather result: {result}")
    
    # Test with units
    result = tool.execute(location="London", units="fahrenheit")
    print(f"Weather result: {result}")
    
    # Test validation
    try:
        tool.execute()  # Missing location - should fail
    except ValueError as e:
        print(f"Validation worked: {e}")

if __name__ == "__main__":
    test_weather_tool()
```

### 4.2: Test in Workflow

Using the CLI:

```bash
# List workflows (should show your new weather workflows)
python -m app.main workflow list

# Run the weather report workflow
python -m app.main workflow run weather_report --param "location=New York" --param "units=fahrenheit"

# Run weather with advice workflow
python -m app.main workflow run weather_with_advice --param "location=Tokyo"
```

## Step 5: Advanced Tool Patterns

### 5.1: Tools with External Dependencies

For tools that call real APIs:

```python
import requests
from typing import Dict, Any
from app.tools.base import BaseTool

class RealWeatherTool(BaseTool):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('WEATHER_API_KEY')
        if not self.api_key:
            raise ValueError("Weather API key required")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        location = kwargs.get('location')
        
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Weather API error: {response.status_code}")
        
        data = response.json()
        
        return {
            "output": f"Weather in {location}: {data['weather'][0]['description']}, {data['main']['temp']}°C",
            "provider": "openweathermap",
            "model": "v2.5",
            "simulated": False,
            "metadata": data
        }
```

### 5.2: Tools with Configuration

For tools that need configuration:

```python
class ConfigurableTool(BaseTool):
    def __init__(self, config_path: str = "tool_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Use self.config in your tool logic
        pass
```

### 5.3: Tools with Memory Integration

Tools can access the memory system:

```python
class MemoryAwareTool(BaseTool):
    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        if self.memory_manager:
            # Access previous workflow context
            context = self.memory_manager.get_workflow_summary()
            # Use context in your tool logic
        
        return {"output": "Tool result with memory context"}
```

## Step 6: Best Practices

### 6.1: Error Handling

Always handle errors gracefully:

```python
def execute(self, **kwargs) -> Dict[str, Any]:
    try:
        # Your tool logic
        result = some_operation()
        return {"output": result}
    except SomeSpecificError as e:
        return {
            "output": f"Tool failed: {str(e)}",
            "error": True,
            "error_type": "SomeSpecificError"
        }
    except Exception as e:
        return {
            "output": f"Unexpected error: {str(e)}",
            "error": True,
            "error_type": "UnexpectedError"
        }
```

### 6.2: Documentation

Document your tools well:

```python
class WellDocumentedTool(BaseTool):
    """
    Brief description of what the tool does.
    
    Required Inputs:
    - param1 (str): Description of param1
    - param2 (int): Description of param2
    
    Optional Inputs:
    - param3 (bool): Description of param3 (default: False)
    
    Output Format:
    {
        "output": "Main tool result",
        "metadata": {"additional": "information"}
    }
    
    Examples:
        Basic usage:
        tool.execute(param1="value", param2=42)
        
        With optional parameter:
        tool.execute(param1="value", param2=42, param3=True)
    """
```

### 6.3: Testing

Create comprehensive tests:

```python
import pytest
from app.tools.your_tool import YourTool

class TestYourTool:
    def setup_method(self):
        self.tool = YourTool()
    
    def test_basic_execution(self):
        result = self.tool.execute(param1="test")
        assert "output" in result
        assert result["output"] is not None
    
    def test_input_validation(self):
        with pytest.raises(ValueError):
            self.tool.execute()  # Missing required param
    
    def test_error_handling(self):
        # Test how tool handles errors
        pass
```

## Step 7: Real-World Example

Here's a complete example of a tool that processes text files:

```python
"""
Text processor tool for file operations.
"""

import os
from pathlib import Path
from typing import Dict, Any
from app.tools.base import BaseTool

class TextProcessorTool(BaseTool):
    """
    Tool for processing text files with various operations.
    
    Supports operations: read, write, append, word_count, line_count
    """
    
    def validate_inputs(self, **kwargs) -> None:
        operation = kwargs.get('operation')
        if not operation:
            raise ValueError("operation parameter is required")
        
        valid_operations = ['read', 'write', 'append', 'word_count', 'line_count']
        if operation not in valid_operations:
            raise ValueError(f"operation must be one of: {valid_operations}")
        
        if 'file_path' not in kwargs:
            raise ValueError("file_path parameter is required")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        self.validate_inputs(**kwargs)
        
        operation = kwargs['operation']
        file_path = Path(kwargs['file_path'])
        
        try:
            if operation == 'read':
                content = file_path.read_text()
                return {
                    "output": content,
                    "operation": "read",
                    "file_path": str(file_path),
                    "file_size": len(content)
                }
            
            elif operation == 'write':
                content = kwargs.get('content', '')
                file_path.write_text(content)
                return {
                    "output": f"Successfully wrote {len(content)} characters to {file_path}",
                    "operation": "write",
                    "file_path": str(file_path),
                    "bytes_written": len(content)
                }
            
            elif operation == 'word_count':
                content = file_path.read_text()
                word_count = len(content.split())
                return {
                    "output": f"File contains {word_count} words",
                    "operation": "word_count",
                    "file_path": str(file_path),
                    "word_count": word_count
                }
            
            # Add other operations...
            
        except FileNotFoundError:
            return {
                "output": f"File not found: {file_path}",
                "error": True,
                "error_type": "FileNotFound"
            }
        except PermissionError:
            return {
                "output": f"Permission denied: {file_path}",
                "error": True,
                "error_type": "PermissionDenied"
            }
        except Exception as e:
            return {
                "output": f"Unexpected error: {str(e)}",
                "error": True,
                "error_type": "UnexpectedError"
            }
```

## Conclusion

You now have all the knowledge needed to create powerful custom tools for the LLM Orchestrator:

1. **Simple Interface**: Inherit from `BaseTool` and implement `execute()`
2. **Input Validation**: Use `validate_inputs()` for robust error handling
3. **Registration**: Add your tool to the tool registry
4. **Integration**: Use your tool in workflows with memory context
5. **Testing**: Create comprehensive tests for reliability

The tool system is designed to be extensible and powerful while maintaining simplicity. Whether you're integrating APIs, processing data, or performing complex operations, this architecture supports it all.

Happy tool building! 🛠️
