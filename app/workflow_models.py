from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class Param(BaseModel):
    type: str
    description: str
    required: bool = False
    default: Any = None


class Step(BaseModel):
    name: str
    tool: str
    inputs: Dict[str, Any]
    memory: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    gate: Optional[Dict[str, str]] = None  # For scrutiny gates
    on_failure: str = "abort_chain"  # Default error handling


class Workflow(BaseModel):
    params: Union[
        List[Union[str, Dict[str, Any]]], Dict[str, Param]
    ]  # Handle both formats
    steps: List[Step]


class Config(BaseModel):
    main_llm: Optional[Dict[str, str]] = None
    workflows: Dict[str, Workflow]
    # Add other top-level config sections here later, e.g., 'reformulation'
