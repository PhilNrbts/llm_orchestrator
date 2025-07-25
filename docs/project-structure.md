# Project Structure

This document outlines the directory structure of the `llm-orchestrator` project.

```
/
├── app/                    # Core application logic
│   ├── __init__.py
│   ├── chat.py             # Interactive chat functionality
│   ├── clients.py          # Clients for different LLM providers
│   ├── executor.py         # Enhanced workflow step execution with memory injection
│   ├── key_management.py   # Secure vault and key handling
│   ├── loader.py           # Configuration loading and validation
│   ├── main.py             # Main CLI entry point (using Click)
│   ├── memory_manager.py   # 🧠 Intelligent memory orchestration and context management
│   ├── memory_store.py     # 🗃️ SQLite-based persistent memory storage system
│   ├── orchestrator.py     # Logic for running queries
│   ├── session.py          # Manages user session and configuration
│   ├── workflow_engine.py  # Enhanced workflow execution engine with memory integration
│   ├── workflow_models.py  # Pydantic models for workflow definitions (with memory support)
│   └── tools/              # Tool implementations for workflow steps
│       ├── __init__.py
│       ├── base.py         # Base tool interface and common functionality
│       ├── model_call.py   # LLM model calling tool with provider abstraction
│       └── parallel_query.py # Multi-model parallel querying tool
├── conversations/          # Stores conversation history (auto-generated)
├── docs/                   # Project documentation
│   ├── architecture/       # C4 model diagrams and ADRs
│   ├── cline/              # Phase-specific implementation documentation
│   │   └── phase4-advanced-memory-management.md # 📖 Complete Phase 4 documentation
│   ├── usage/              # User guides (installation, configuration)
│   ├── contributing.md     # Guidelines for contributors
│   └── project-structure.md # This file - project organization reference
├── scripts/                # Helper scripts for development and setup
│   ├── __init__.py
│   ├── create_summary.py   # Summary generation utilities
│   ├── generate_summary.py # Enhanced summary generation
│   ├── init_vault.py       # Vault initialization
│   ├── run_workflow.py     # Workflow execution script
│   ├── test_memory_system.py # 🧪 Comprehensive memory system test suite
│   ├── test_real_tools.py  # Real API integration testing
│   ├── test_workflow_engine.py # Workflow engine testing
│   └── vault_manager.py    # Vault management utilities
├── tests/                  # Unit and integration tests
│   ├── test_cli.py         # CLI functionality tests
│   ├── test_core_logic.py  # Core logic unit tests
│   └── test_providers.py   # Provider integration tests
├── private/                # Private files (gitignored)
├── workspace/              # Temporary workspace directory
├── .gitignore              # Files and directories ignored by Git
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── config.yaml             # Main configuration file (with memory-aware workflows)
├── memory.db               # 💾 SQLite database for persistent workflow memory (auto-generated)
├── models.yaml             # Configuration for LLM models
├── poetry.lock             # Poetry lock file for dependency management
├── pyproject.toml          # Project metadata and dependencies for Poetry
├── README.md               # Main project README
├── ROADMAP.md              # High-level project roadmap (Phase 4 ✅ COMPLETED)
├── settings.py             # Application settings and configuration
└── setup_interactive.sh    # Interactive setup script
```

## Key Architecture Components (Phase 4: Memory Management)

### 🧠 Memory Management System
- **`app/memory_store.py`**: SQLite-based persistent storage for workflow context
- **`app/memory_manager.py`**: Intelligent memory orchestration and template variable injection
- **`memory.db`**: Auto-generated SQLite database storing workflow memory slices

### 🔧 Enhanced Workflow Engine
- **`app/workflow_engine.py`**: Core workflow execution with memory integration
- **`app/executor.py`**: Step execution with memory context injection
- **`app/workflow_models.py`**: Pydantic models supporting memory configurations

### 🛠️ Tool System
- **`app/tools/base.py`**: Base tool interface and common functionality
- **`app/tools/model_call.py`**: LLM model calling with provider abstraction
- **`app/tools/parallel_query.py`**: Multi-model parallel querying capabilities

### 📋 Memory-Aware Configuration
The `config.yaml` now supports sophisticated memory patterns:
```yaml
workflows:
  sequential_elaboration:
    steps:
      - name: step1
        memory:
          needs: ["user_prompt", "tool_output(previous_step)"]
        inputs:
          prompt: "{{memory.user_prompt}} - {{memory.previous_step_output}}"
```

### 🧪 Testing & Development
- **`scripts/test_memory_system.py`**: Comprehensive memory system test suite
- **`scripts/test_real_tools.py`**: Real API integration testing
- **`scripts/run_workflow.py`**: Workflow execution and testing script

This architecture enables intelligent, context-aware workflows where each step can precisely access the memory context it needs, enabling sophisticated multi-step AI orchestration with persistent state management.
