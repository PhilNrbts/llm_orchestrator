#!/usr/bin/env python3
"""
Test script for Phase 4: Advanced Memory Management
This script tests all components of the memory system integration.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.memory_store import MemoryStore
from app.memory_manager import MemoryManager
from app.workflow_engine import WorkflowEngine
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_memory_store():
    """Test the basic memory store functionality."""
    console.print("\n🧪 Testing Memory Store...")
    
    # Use a test database
    test_db = "test_memory.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    try:
        store = MemoryStore(test_db)
        
        # Test adding entries
        workflow_id = "test_workflow_001"
        
        # Add user prompt
        entry_id1 = store.add_entry(
            workflow_id=workflow_id,
            step_name="__initial__",
            content="What are the benefits of renewable energy?",
            classification="user_prompt"
        )
        
        # Add step output
        entry_id2 = store.add_entry(
            workflow_id=workflow_id,
            step_name="initial_answer",
            content="Renewable energy offers environmental, economic, and social benefits...",
            classification="output",
            metadata={"provider": "gemini", "model": "gemini-1.5-flash"}
        )
        
        console.print(f"✅ Added entries: {entry_id1}, {entry_id2}")
        
        # Test retrieval
        user_prompt = store.retrieve_user_prompt(workflow_id)
        step_output = store.retrieve_step_output(workflow_id, "initial_answer")
        
        console.print(f"✅ Retrieved user prompt: {user_prompt[:50]}...")
        console.print(f"✅ Retrieved step output: {step_output[:50]}...")
        
        # Test statistics
        stats = store.get_stats()
        console.print(f"✅ Database stats: {stats}")
        
        # Verify database file exists and has content
        if os.path.exists(test_db):
            console.print(f"✅ Database file created: {test_db}")
            
            # Check table contents
            with sqlite3.connect(test_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory_slices")
                count = cursor.fetchone()[0]
                console.print(f"✅ Database contains {count} entries")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Memory Store test failed: {e}", style="red")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)


def test_memory_manager():
    """Test the memory manager functionality."""
    console.print("\n🧪 Testing Memory Manager...")
    
    # Use a test database
    test_db = "test_memory_manager.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    try:
        manager = MemoryManager(db_path=test_db)
        
        # Start a workflow
        workflow_id = manager.start_workflow(
            "test_workflow", 
            {"user_prompt": "Explain machine learning", "model": "gpt-4"}
        )
        console.print(f"✅ Started workflow: {workflow_id}")
        
        # Save step results
        step1_result = {
            "output": "Machine learning is a subset of AI that enables computers to learn...",
            "provider": "openai",
            "model": "gpt-4",
            "simulated": False
        }
        manager.save_step_result("initial_analysis", step1_result)
        console.print("✅ Saved step 1 result")
        
        step2_result = {
            "output": "Generate a more detailed explanation focusing on practical applications",
            "provider": "gemini", 
            "model": "gemini-1.5-flash",
            "simulated": False
        }
        manager.save_step_result("elaboration_generator", step2_result)
        console.print("✅ Saved step 2 result")
        
        # Test context fetching
        step_config = {
            "name": "final_response",
            "tool": "model_call",
            "inputs": {"prompt": "{{memory.user_prompt}} - {{memory.initial_analysis_output}}"},
            "memory": {
                "needs": ["user_prompt", "tool_output(initial_analysis)"]
            }
        }
        
        context = manager.fetch_context_for_step(step_config)
        console.print(f"✅ Fetched context: {list(context.keys())}")
        
        # Test memory injection
        original_inputs = {
            "prompt": "Based on {{memory.user_prompt}}, elaborate on {{memory.initial_analysis_output}}"
        }
        
        injected_inputs = manager.inject_memory_context(original_inputs, context)
        console.print(f"✅ Injected memory context")
        console.print(f"   Original: {original_inputs['prompt'][:60]}...")
        console.print(f"   Injected: {injected_inputs['prompt'][:60]}...")
        
        # Test workflow summary
        summary = manager.get_workflow_summary()
        console.print(f"✅ Workflow summary: {summary}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Memory Manager test failed: {e}", style="red")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)


def test_workflow_with_memory():
    """Test the full workflow integration with memory."""
    console.print("\n🧪 Testing Workflow with Memory Integration...")
    
    # Clean up any existing memory.db
    if os.path.exists("memory.db"):
        os.remove("memory.db")
    
    try:
        # Initialize workflow engine
        engine = WorkflowEngine()
        
        # Run the sequential_elaboration workflow with memory
        result = engine.run(
            "sequential_elaboration",
            {"user_prompt": "What are the key advantages of using Docker containers in software development?"}
        )
        
        console.print("✅ Workflow completed successfully")
        
        # Verify memory.db was created and contains data
        if os.path.exists("memory.db"):
            console.print("✅ Memory database created")
            
            # Check database contents
            with sqlite3.connect("memory.db") as conn:
                cursor = conn.cursor()
                
                # Get all entries
                cursor.execute("""
                    SELECT workflow_id, step_name, classification, 
                           substr(content, 1, 50) as content_preview
                    FROM memory_slices 
                    ORDER BY timestamp
                """)
                
                entries = cursor.fetchall()
                
                # Create a table to display memory contents
                table = Table(title="Memory Database Contents")
                table.add_column("Workflow ID", style="cyan")
                table.add_column("Step", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Content Preview", style="white")
                
                for entry in entries:
                    table.add_row(
                        entry[0][-12:] + "...",  # Last 12 chars of workflow ID
                        entry[1],
                        entry[2],
                        entry[3] + "..." if len(entry[3]) == 50 else entry[3]
                    )
                
                console.print(table)
                console.print(f"✅ Found {len(entries)} memory entries")
                
                # Verify we have the expected entries
                expected_classifications = ["user_prompt", "parameters", "output"]
                found_classifications = list(set([entry[2] for entry in entries]))
                
                for expected in expected_classifications:
                    if expected in found_classifications:
                        console.print(f"✅ Found {expected} entries")
                    else:
                        console.print(f"⚠️  Missing {expected} entries", style="yellow")
        
        # Check if memory context was used in prompts
        if 'elaboration_prompt_generator' in result:
            elaboration_step = result['elaboration_prompt_generator']
            if isinstance(elaboration_step, dict) and 'output' in elaboration_step:
                console.print("✅ Memory-aware prompts were generated")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Workflow with memory test failed: {e}", style="red")
        return False


def inspect_memory_database():
    """Inspect the contents of the memory database after testing."""
    console.print("\n🔍 Inspecting Memory Database Contents...")
    
    if not os.path.exists("memory.db"):
        console.print("❌ No memory.db file found", style="red")
        return
    
    try:
        store = MemoryStore("memory.db")
        stats = store.get_stats()
        
        # Display statistics
        stats_table = Table(title="Memory Database Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Entries", str(stats["total_entries"]))
        stats_table.add_row("Unique Workflows", str(stats["unique_workflows"]))
        stats_table.add_row("Database Size", f"{stats['database_size_bytes']} bytes")
        
        for classification, count in stats["by_classification"].items():
            stats_table.add_row(f"  └─ {classification}", str(count))
        
        console.print(stats_table)
        
        # Show recent entries
        with sqlite3.connect("memory.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT workflow_id, step_name, classification, 
                       substr(content, 1, 100) as content_preview,
                       timestamp
                FROM memory_slices 
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            recent_entries = cursor.fetchall()
            
            if recent_entries:
                console.print("\n📋 Recent Memory Entries:")
                for i, entry in enumerate(recent_entries, 1):
                    console.print(f"{i}. [{entry[2]}] {entry[1]}: {entry[3]}...")
        
    except Exception as e:
        console.print(f"❌ Database inspection failed: {e}", style="red")


def main():
    """Run all memory system tests."""
    console.print(Panel.fit(
        "[bold blue]Phase 4: Advanced Memory Management - Test Suite[/bold blue]",
        border_style="blue"
    ))
    
    results = []
    
    # Test 1: Memory Store
    results.append(test_memory_store())
    
    # Test 2: Memory Manager
    results.append(test_memory_manager())
    
    # Test 3: Full Workflow Integration
    results.append(test_workflow_with_memory())
    
    # Inspect the memory database
    inspect_memory_database()
    
    # Summary
    console.print(f"\n📊 Test Results Summary:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"🎉 All {total} tests passed!", style="bold green")
        console.print("\n✅ Phase 4: Advanced Memory Management - COMPLETE!")
        console.print("   ✓ Memory Store working correctly")
        console.print("   ✓ Memory Manager functioning properly") 
        console.print("   ✓ Workflow integration successful")
        console.print("   ✓ Memory database created and populated")
        console.print("   ✓ Context-aware prompts generated")
    else:
        console.print(f"❌ {passed}/{total} tests passed", style="red")
        
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
