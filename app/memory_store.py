"""
Memory Store module for persistent workflow memory management.
This module provides SQLite-based storage for workflow execution context and results.
"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class MemoryStore:
    """
    SQLite-based memory store for workflow execution context.

    Stores memory slices with metadata including workflow ID, step name,
    content, classification, and timestamps for context-aware workflow execution.
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        Initialize the memory store and create necessary tables.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Create the memory table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_slices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    classification TEXT DEFAULT 'output',
                    metadata TEXT DEFAULT '{}',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT NOT NULL
                )
            """
            )

            # Create indexes for efficient querying
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflow_step
                ON memory_slices(workflow_id, step_name)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_classification
                ON memory_slices(classification)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON memory_slices(timestamp DESC)
            """
            )

            conn.commit()

    def add_entry(
        self,
        workflow_id: str,
        step_name: str,
        content: Union[str, Dict, List],
        classification: str = "output",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save a new memory slice to the database.

        Args:
            workflow_id: Unique identifier for the workflow execution
            step_name: Name of the workflow step
            content: The content to store (will be JSON-serialized if not string)
            classification: Type of memory slice ('output', 'input', 'user_prompt', 'error', etc.)
            metadata: Additional metadata as dictionary

        Returns:
            The database ID of the created entry
        """
        # Serialize content if it's not a string
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_str = str(content)

        # Serialize metadata
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)

        # Current timestamp for created_at
        created_at = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memory_slices
                (workflow_id, step_name, content, classification, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow_id,
                    step_name,
                    content_str,
                    classification,
                    metadata_str,
                    created_at,
                ),
            )

            entry_id = cursor.lastrowid
            conn.commit()

        return str(entry_id)

    def retrieve(
        self,
        workflow_id: Optional[str] = None,
        step_name: Optional[str] = None,
        classification: Optional[str] = None,
        limit: Optional[int] = None,
        order_by: str = "timestamp DESC",
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memory slices based on specified criteria.

        Args:
            workflow_id: Filter by workflow ID
            step_name: Filter by step name
            classification: Filter by classification type
            limit: Maximum number of results to return
            order_by: SQL ORDER BY clause (default: newest first)

        Returns:
            List of memory slice dictionaries
        """
        query_parts = ["SELECT * FROM memory_slices WHERE 1=1"]
        params = []

        if workflow_id:
            query_parts.append("AND workflow_id = ?")
            params.append(workflow_id)

        if step_name:
            query_parts.append("AND step_name = ?")
            params.append(step_name)

        if classification:
            query_parts.append("AND classification = ?")
            params.append(classification)

        query_parts.append(f"ORDER BY {order_by}")

        if limit:
            query_parts.append("LIMIT ?")
            params.append(limit)

        query = " ".join(query_parts)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                result = dict(row)

                # Try to deserialize metadata
                try:
                    result["metadata"] = json.loads(result["metadata"])
                except (json.JSONDecodeError, TypeError):
                    result["metadata"] = {}

                # Try to deserialize content if it looks like JSON
                try:
                    if result["content"].strip().startswith(("{", "[")):
                        result["content_parsed"] = json.loads(result["content"])
                    else:
                        result["content_parsed"] = result["content"]
                except (json.JSONDecodeError, AttributeError):
                    result["content_parsed"] = result["content"]

                results.append(result)

            return results

    def retrieve_latest(
        self,
        workflow_id: str,
        step_name: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent memory slice matching the criteria.

        Args:
            workflow_id: Workflow ID to search in
            step_name: Optional step name filter
            classification: Optional classification filter

        Returns:
            Most recent memory slice or None if not found
        """
        results = self.retrieve(
            workflow_id=workflow_id,
            step_name=step_name,
            classification=classification,
            limit=1,
            order_by="timestamp DESC",
        )

        return results[0] if results else None

    def retrieve_step_output(self, workflow_id: str, step_name: str) -> Optional[str]:
        """
        Convenience method to retrieve the output of a specific step.

        Args:
            workflow_id: Workflow ID
            step_name: Name of the step

        Returns:
            Step output content or None if not found
        """
        result = self.retrieve_latest(
            workflow_id=workflow_id, step_name=step_name, classification="output"
        )

        return result["content"] if result else None

    def retrieve_user_prompt(self, workflow_id: str) -> Optional[str]:
        """
        Convenience method to retrieve the original user prompt for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            User prompt content or None if not found
        """
        result = self.retrieve_latest(
            workflow_id=workflow_id, classification="user_prompt"
        )

        return result["content"] if result else None

    def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete execution history for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of all memory slices for the workflow, ordered by timestamp
        """
        return self.retrieve(workflow_id=workflow_id, order_by="timestamp ASC")

    def cleanup_old_entries(self, days_old: int = 30) -> int:
        """
        Remove memory entries older than specified days.

        Args:
            days_old: Number of days after which to remove entries

        Returns:
            Number of entries removed
        """
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM memory_slices
                WHERE datetime(timestamp) < datetime(?)
            """,
                (cutoff_date.isoformat(),),
            )

            deleted_count = cursor.rowcount
            conn.commit()

        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory store.

        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total entries
            cursor.execute("SELECT COUNT(*) FROM memory_slices")
            total_entries = cursor.fetchone()[0]

            # Entries by classification
            cursor.execute(
                """
                SELECT classification, COUNT(*)
                FROM memory_slices
                GROUP BY classification
            """
            )
            by_classification = dict(cursor.fetchall())

            # Unique workflows
            cursor.execute("SELECT COUNT(DISTINCT workflow_id) FROM memory_slices")
            unique_workflows = cursor.fetchone()[0]

            # Database size
            db_size = (
                Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            )

            return {
                "total_entries": total_entries,
                "unique_workflows": unique_workflows,
                "by_classification": by_classification,
                "database_size_bytes": db_size,
                "database_path": self.db_path,
            }
