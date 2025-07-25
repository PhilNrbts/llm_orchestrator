"""
Memory Manager module for intelligent workflow memory orchestration.
This module provides the "brain" that interprets memory requirements and coordinates
with the MemoryStore to provide context-aware workflow execution.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .memory_store import MemoryStore


class MemoryManager:
    """
    Intelligent memory manager that orchestrates workflow memory operations.
    
    Interprets memory requirements from config.yaml and coordinates with MemoryStore
    to provide context-aware execution with persistent memory across workflow steps.
    """
    
    def __init__(self, memory_store: Optional[MemoryStore] = None, db_path: str = "memory.db"):
        """
        Initialize the memory manager.
        
        Args:
            memory_store: Optional MemoryStore instance (will create if not provided)
            db_path: Path to the SQLite database (used if memory_store not provided)
        """
        self.memory_store = memory_store or MemoryStore(db_path)
        self.current_workflow_id: Optional[str] = None
        self.workflow_history: List[Dict[str, Any]] = []
    
    def start_workflow(self, workflow_name: str, initial_params: Dict[str, Any]) -> str:
        """
        Start a new workflow execution and initialize memory tracking.
        
        Args:
            workflow_name: Name of the workflow being executed
            initial_params: Initial parameters passed to the workflow
            
        Returns:
            Unique workflow ID for this execution
        """
        # Generate unique workflow ID
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.current_workflow_id = workflow_id
        self.workflow_history = []
        
        # Store initial parameters and user prompt
        if 'user_prompt' in initial_params:
            self.memory_store.add_entry(
                workflow_id=workflow_id,
                step_name="__initial__",
                content=initial_params['user_prompt'],
                classification="user_prompt",
                metadata={
                    "workflow_name": workflow_name,
                    "all_params": initial_params
                }
            )
        
        # Store all initial parameters
        self.memory_store.add_entry(
            workflow_id=workflow_id,
            step_name="__initial__",
            content=initial_params,
            classification="parameters",
            metadata={
                "workflow_name": workflow_name
            }
        )
        
        return workflow_id
    
    def save_step_result(
        self,
        step_name: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save the result of a workflow step to memory.
        
        Args:
            step_name: Name of the step that was executed
            result: Result dictionary from tool execution
            metadata: Additional metadata about the step execution
            
        Returns:
            Database ID of the saved entry
        """
        if not self.current_workflow_id:
            raise ValueError("No active workflow. Call start_workflow() first.")
        
        # Extract the main output content
        output_content = result.get('output', str(result))
        
        # Prepare metadata
        step_metadata = {
            "provider": result.get('provider'),
            "model": result.get('model'),
            "simulated": result.get('simulated', False),
            "token_count": result.get('token_count'),
            "execution_time": result.get('execution_time'),
            **(metadata or {})
        }
        
        # Save the step output
        entry_id = self.memory_store.add_entry(
            workflow_id=self.current_workflow_id,
            step_name=step_name,
            content=output_content,
            classification="output",
            metadata=step_metadata
        )
        
        # Update workflow history
        self.workflow_history.append({
            "step_name": step_name,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "entry_id": entry_id
        })
        
        return entry_id
    
    def fetch_context_for_step(
        self,
        step_config: Dict[str, Any],
        workflow_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Fetch required context for a workflow step based on its memory configuration.
        
        Args:
            step_config: Step configuration from config.yaml
            workflow_history: Optional workflow history (uses current if not provided)
            
        Returns:
            Dictionary of context variables to inject into step inputs
        """
        if not self.current_workflow_id:
            return {}
        
        # Use provided history or current workflow history
        history = workflow_history or self.workflow_history
        
        # Get memory requirements from step config
        memory_config = step_config.get('memory', {})
        needs = memory_config.get('needs', [])
        
        if not needs:
            return {}
        
        context = {}
        
        for need in needs:
            try:
                context_value = self._resolve_memory_need(need, history)
                if context_value is not None:
                    # Create variable name from need specification
                    var_name = self._create_variable_name(need)
                    context[var_name] = context_value
            except Exception as e:
                print(f"Warning: Failed to resolve memory need '{need}': {e}")
                continue
        
        return context
    
    def _resolve_memory_need(
        self,
        need: str,
        workflow_history: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Resolve a specific memory need specification.
        
        Args:
            need: Memory need specification (e.g., "last_user_prompt", "tool_output(step_name)")
            workflow_history: Current workflow execution history
            
        Returns:
            Resolved content or None if not found
        """
        need = need.strip()
        
        # Handle "last_user_prompt" or "user_prompt"
        if need in ["last_user_prompt", "user_prompt"]:
            return self.memory_store.retrieve_user_prompt(self.current_workflow_id)
        
        # Handle "tool_output(step_name)" pattern
        tool_output_match = re.match(r'tool_output\(([^)]+)\)', need)
        if tool_output_match:
            step_name = tool_output_match.group(1).strip()
            return self.memory_store.retrieve_step_output(self.current_workflow_id, step_name)
        
        # Handle "step_output(step_name)" pattern (alias for tool_output)
        step_output_match = re.match(r'step_output\(([^)]+)\)', need)
        if step_output_match:
            step_name = step_output_match.group(1).strip()
            return self.memory_store.retrieve_step_output(self.current_workflow_id, step_name)
        
        # Handle "last_output" - get the most recent step output
        if need == "last_output":
            if workflow_history:
                last_step = workflow_history[-1]
                return last_step['result'].get('output')
            return None
        
        # Handle "previous_output" (alias for last_output)
        if need == "previous_output":
            if workflow_history:
                last_step = workflow_history[-1]
                return last_step['result'].get('output')
            return None
        
        # Handle "step(step_name)" - get complete step result
        step_match = re.match(r'step\(([^)]+)\)', need)
        if step_match:
            step_name = step_match.group(1).strip()
            result = self.memory_store.retrieve_latest(
                workflow_id=self.current_workflow_id,
                step_name=step_name,
                classification="output"
            )
            return result['content'] if result else None
        
        # Handle direct step name reference
        if need and not any(char in need for char in "()[]{}"):
            # Treat as direct step name
            return self.memory_store.retrieve_step_output(self.current_workflow_id, need)
        
        return None
    
    def _create_variable_name(self, need: str) -> str:
        """
        Create a variable name for a memory need to use in template injection.
        
        Args:
            need: Memory need specification
            
        Returns:
            Variable name suitable for template substitution
        """
        # Handle specific patterns
        if need in ["last_user_prompt", "user_prompt"]:
            return "memory.user_prompt"
        
        if need in ["last_output", "previous_output"]:
            return "memory.last_output"
        
        # Handle function-style needs
        tool_output_match = re.match(r'tool_output\(([^)]+)\)', need)
        if tool_output_match:
            step_name = tool_output_match.group(1).strip()
            return f"memory.{step_name}_output"
        
        step_output_match = re.match(r'step_output\(([^)]+)\)', need)
        if step_output_match:
            step_name = step_output_match.group(1).strip()
            return f"memory.{step_name}_output"
        
        step_match = re.match(r'step\(([^)]+)\)', need)
        if step_match:
            step_name = step_match.group(1).strip()
            return f"memory.{step_name}"
        
        # Handle direct step name
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', need)
        return f"memory.{clean_name}"
    
    def inject_memory_context(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inject memory context into step inputs by replacing template variables.
        
        Args:
            inputs: Original step inputs
            context: Memory context to inject
            
        Returns:
            Step inputs with memory context injected
        """
        if not context:
            return inputs
        
        # Create a deep copy to avoid modifying original
        import copy
        injected_inputs = copy.deepcopy(inputs)
        
        # Recursively inject context into string values
        def inject_recursive(obj):
            if isinstance(obj, str):
                # Replace memory template variables
                for var_name, var_value in context.items():
                    if var_value is not None:
                        template_var = "{{" + var_name + "}}"
                        obj = obj.replace(template_var, str(var_value))
                return obj
            elif isinstance(obj, dict):
                return {k: inject_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [inject_recursive(item) for item in obj]
            else:
                return obj
        
        return inject_recursive(injected_inputs)
    
    def get_workflow_summary(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of workflow execution including memory usage.
        
        Args:
            workflow_id: Workflow ID (uses current if not provided)
            
        Returns:
            Dictionary with workflow summary
        """
        wf_id = workflow_id or self.current_workflow_id
        if not wf_id:
            return {}
        
        history = self.memory_store.get_workflow_history(wf_id)
        
        # Group by classification
        by_classification = {}
        for entry in history:
            classification = entry['classification']
            if classification not in by_classification:
                by_classification[classification] = []
            by_classification[classification].append(entry)
        
        # Extract steps
        steps = [entry for entry in history if entry['classification'] == 'output']
        step_names = [step['step_name'] for step in steps]
        
        return {
            "workflow_id": wf_id,
            "total_entries": len(history),
            "step_count": len(steps),
            "step_names": step_names,
            "by_classification": {k: len(v) for k, v in by_classification.items()},
            "start_time": history[0]['created_at'] if history else None,
            "end_time": history[-1]['created_at'] if history else None,
            "has_user_prompt": 'user_prompt' in by_classification
        }
    
    def clear_workflow_memory(self, workflow_id: Optional[str] = None):
        """
        Clear memory for a specific workflow (mainly for testing).
        
        Args:
            workflow_id: Workflow ID (uses current if not provided)
        """
        wf_id = workflow_id or self.current_workflow_id
        if not wf_id:
            return
        
        # This is a destructive operation, so we'll need to implement it in MemoryStore
        # For now, we'll just reset the current workflow tracking
        if wf_id == self.current_workflow_id:
            self.current_workflow_id = None
            self.workflow_history = []
