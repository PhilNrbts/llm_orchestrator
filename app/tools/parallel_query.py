"""
Parallel query tool for executing multiple LLM calls simultaneously.
This tool orchestrates multiple model_call operations in parallel.
"""

import concurrent.futures
from typing import Dict, Any, Optional
from rich.console import Console

from .base import BaseTool
from .model_call import ModelCallTool

console = Console()


class ParallelQueryTool(BaseTool):
    """
    Tool for executing multiple LLM queries in parallel.

    Required inputs:
    - queries: List of query configurations, each containing:
      - provider: The LLM provider
      - model: The specific model to use
      - prompt_template: The prompt to send (can contain template variables)

    Optional inputs:
    - max_workers: Maximum number of concurrent workers (default: 4)
    """

    def __init__(self, vault_password: Optional[str] = None):
        """
        Initialize the parallel query tool.

        Args:
            vault_password: Password for decrypting API keys
        """
        self.model_call_tool = ModelCallTool(vault_password)

    def validate_inputs(self, **kwargs) -> None:
        """Validate required inputs for parallel query."""
        if "queries" not in kwargs:
            raise ValueError("Missing required field 'queries' for parallel_query")

        queries = kwargs.get("queries", [])
        if not isinstance(queries, list) or len(queries) == 0:
            raise ValueError("'queries' must be a non-empty list")

        # Validate each query
        for i, query in enumerate(queries):
            if not isinstance(query, dict):
                raise ValueError(f"Query {i} must be a dictionary")

            required_fields = ["provider", "model", "prompt_template"]
            missing_fields = [field for field in required_fields if field not in query]

            if missing_fields:
                raise ValueError(f"Query {i} missing required fields: {missing_fields}")

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute multiple model calls in parallel.

        Args:
            **kwargs: Parallel query parameters

        Returns:
            Dict containing list of outputs from all queries
        """
        # Validate inputs
        self.validate_inputs(**kwargs)

        queries = kwargs.get("queries", [])
        max_workers = kwargs.get("max_workers", 4)

        console.print(f"🔄 Starting {len(queries)} parallel queries...", style="blue")

        def execute_single_query(query_config: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a single query using the model_call tool."""
            try:
                # Prepare the model call parameters
                model_call_params = {
                    "provider": query_config["provider"],
                    "model": query_config["model"],
                    "prompt": query_config[
                        "prompt_template"
                    ],  # Note: template resolution happens in executor
                    "max_tokens": query_config.get("max_tokens", 1024),
                    "temperature": query_config.get("temperature", 0.7),
                }

                # Execute the model call
                result = self.model_call_tool.execute(**model_call_params)

                # Add query metadata to result
                result["query_config"] = {
                    "provider": query_config["provider"],
                    "model": query_config["model"],
                }

                return result

            except Exception as e:
                console.print(
                    f"❌ Query failed for {query_config.get('provider', 'unknown')}/{query_config.get('model', 'unknown')}: {str(e)}",
                    style="red",
                )
                return {
                    "output": f"[ERROR] Query failed: {str(e)}",
                    "provider": query_config.get("provider", "unknown"),
                    "model": query_config.get("model", "unknown"),
                    "error": str(e),
                    "simulated": True,
                }

        # Execute queries in parallel using ThreadPoolExecutor
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all queries
            future_to_query = {
                executor.submit(execute_single_query, query): i
                for i, query in enumerate(queries)
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_query):
                query_index = future_to_query[future]
                try:
                    result = future.result()
                    results.append((query_index, result))
                    console.print(
                        f"✅ Query {query_index + 1}/{len(queries)} completed",
                        style="green",
                    )
                except Exception as e:
                    console.print(
                        f"❌ Query {query_index + 1} failed: {str(e)}", style="red"
                    )
                    results.append(
                        (
                            query_index,
                            {
                                "output": f"[ERROR] Execution failed: {str(e)}",
                                "error": str(e),
                                "simulated": True,
                            },
                        )
                    )

        # Sort results by original query order
        results.sort(key=lambda x: x[0])
        ordered_results = [result for _, result in results]

        console.print(
            f"🎉 All {len(queries)} parallel queries completed", style="bold green"
        )

        return {
            "outputs": ordered_results,
            "query_count": len(queries),
            "successful_queries": len([r for r in ordered_results if "error" not in r]),
        }
