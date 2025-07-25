#!/usr/bin/env python3
"""
Simple workflow runner script for the LLM orchestrator.
Usage: python scripts/run_workflow.py <workflow_name> [params...]
"""

import sys
import json
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workflow_engine import WorkflowEngine
from rich.console import Console

console = Console()

def main():
    if len(sys.argv) < 2:
        console.print("Usage: python scripts/run_workflow.py <workflow_name> [param=value ...]")
        console.print("\nExample: python scripts/run_workflow.py sequential_elaboration user_prompt='What is AI?'")
        return
    
    workflow_name = sys.argv[1]
    
    # Parse parameters from command line
    params = {}
    for arg in sys.argv[2:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Try to parse as JSON, fallback to string
            try:
                params[key] = json.loads(value)
            except:
                params[key] = value
    
    try:
        engine = WorkflowEngine()
        result = engine.run(workflow_name, params)
        console.print(f"\n✅ Workflow completed successfully!")
        console.print(f"Result: {result}")
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")

if __name__ == "__main__":
    main()
