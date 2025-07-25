# Fractured Context Memory System

The LLM Orchestrator features an advanced "Fractured Context" memory system that enables workflows to intelligently manage and access context across multiple steps. This system eliminates the traditional "all-or-nothing" approach to context management and allows each workflow step to precisely define what information it needs.

## Overview

Traditional AI workflows suffer from context bloat - either they pass everything to each step (causing inefficiency and confusion) or they pass nothing (losing valuable context). The Fractured Context system solves this by allowing each step to request exactly the context it needs.

### Key Benefits

- **🎯 Precision**: Steps get exactly the context they need, nothing more
- **🧠 Intelligence**: Context is automatically retrieved and injected into prompts
- **💾 Persistence**: All workflow context is stored in a SQLite database
- **🔄 Reusability**: Memory persists across workflow runs for analysis
- **⚡ Performance**: No unnecessary context reduces token usage and improves speed

## How It Works

### 1. Memory Storage

Every workflow execution creates memory "slices" that are stored in a local SQLite database (`memory.db`). These slices include:

- **User Prompts**: The original input that started the workflow
- **Step Outputs**: Results from each workflow step
- **Parameters**: Workflow configuration and input parameters
- **Metadata**: Provider, model, timestamps, and other execution details

### 2. Context Requests

Each workflow step can specify what memory it needs using the `memory.needs` configuration:

```yaml
steps:
  - name: step_name
    memory:
      needs: ["user_prompt", "tool_output(previous_step)"]
    inputs:
      prompt: "Based on {{memory.user_prompt}} and {{memory.previous_step_output}}, ..."
```

### 3. Template Injection

The memory manager automatically resolves `{{memory.variable}}` templates in your step inputs, replacing them with the actual content from the memory database.

## Memory Patterns

### Basic Patterns

#### User Prompt Access
```yaml
memory:
  needs: ["user_prompt"]
inputs:
  prompt: "Answer this question: {{memory.user_prompt}}"
```

#### Previous Step Output
```yaml
memory:
  needs: ["tool_output(step_name)"]
inputs:
  prompt: "Elaborate on: {{memory.step_name_output}}"
```

#### Multiple Context Sources
```yaml
memory:
  needs: ["user_prompt", "tool_output(analysis)", "tool_output(research)"]
inputs:
  prompt: |
    Question: {{memory.user_prompt}}
    Analysis: {{memory.analysis_output}}
    Research: {{memory.research_output}}
    
    Provide a comprehensive answer.
```

### Advanced Patterns

#### Last Output (Most Recent Step)
```yaml
memory:
  needs: ["last_output"]
inputs:
  prompt: "Continue from: {{memory.last_output}}"
```

#### Parameters Access
```yaml
memory:
  needs: ["parameters"]
inputs:
  prompt: "Using model {{memory.initial_model}}, analyze: {{memory.user_prompt}}"
```

#### Custom Classifications
```yaml
memory:
  needs: ["classification(error)", "classification(warning)"]
inputs:
  prompt: "Previous errors: {{memory.error}} Warnings: {{memory.warning}}"
```

## Complete Example

Here's a comprehensive workflow that demonstrates the memory system:

```yaml
workflows:
  research_and_analyze:
    params:
      - topic
      - analysis_depth: "detailed"
      - output_format: "report"
    
    steps:
      # Step 1: Initial research
      - name: research
        tool: "model_call"
        inputs:
          provider: "gemini"
          model: "gemini-1.5-pro"
          prompt: "Research the topic: {{params.topic}}. Provide key facts and findings."
      
      # Step 2: Generate analysis questions based on research
      - name: generate_questions
        tool: "model_call"
        memory:
          needs: ["user_prompt", "tool_output(research)"]
        inputs:
          provider: "anthropic"
          model: "claude-3-sonnet-20240229"
          prompt: |
            Topic: {{memory.topic}}
            Research findings: {{memory.research_output}}
            
            Generate 3 specific analysis questions that would help create a {{params.analysis_depth}} analysis.
      
      # Step 3: Answer analysis questions
      - name: detailed_analysis
        tool: "model_call"
        memory:
          needs: ["tool_output(research)", "tool_output(generate_questions)"]
        inputs:
          provider: "gemini"
          model: "gemini-1.5-pro"
          prompt: |
            Research: {{memory.research_output}}
            Questions: {{memory.generate_questions_output}}
            
            Provide detailed answers to each question based on the research.
      
      # Step 4: Create final report
      - name: create_report
        tool: "model_call"
        memory:
          needs: ["user_prompt", "tool_output(research)", "tool_output(detailed_analysis)", "parameters"]
        inputs:
          provider: "anthropic"
          model: "claude-3-opus-20240229"
          prompt: |
            Topic: {{memory.topic}}
            Format: {{memory.output_format}}
            Depth: {{memory.analysis_depth}}
            
            Research: {{memory.research_output}}
            Analysis: {{memory.detailed_analysis_output}}
            
            Create a comprehensive {{memory.output_format}} on {{memory.topic}}.
```

## Memory Variable Naming

The memory system automatically creates variables based on the pattern:
- `{step_name}_output` for step outputs
- `{parameter_name}` for workflow parameters
- Special variables like `user_prompt`, `last_output`

### Example Variable Generation

For a step named `initial_research`, the output becomes available as:
- `{{memory.initial_research_output}}`

For parameters like `analysis_depth`, they become:
- `{{memory.analysis_depth}}`

## CLI Integration

### View Workflow Memory
```bash
# Show memory statistics
llm-cli workflow inspect --all

# Show recent workflow execution
llm-cli workflow inspect --recent

# Show specific workflow run
llm-cli workflow inspect abc123
```

### Memory Database Structure

The SQLite database (`memory.db`) contains:
- **workflow_id**: Unique identifier for each workflow run
- **step_name**: Name of the workflow step
- **content**: The actual memory content
- **classification**: Type of memory (user_prompt, output, parameters, etc.)
- **metadata**: Additional information (provider, model, timestamps)
- **timestamp**: When the memory was created

## Best Practices

### 1. Request Only What You Need
```yaml
# Good - specific context
memory:
  needs: ["tool_output(analysis)"]

# Avoid - requesting everything when you only need one thing
memory:
  needs: ["user_prompt", "tool_output(step1)", "tool_output(step2)", "tool_output(step3)"]
```

### 2. Use Descriptive Step Names
```yaml
# Good - clear purpose
- name: market_analysis
- name: risk_assessment
- name: recommendation_generator

# Avoid - unclear names
- name: step1
- name: process
- name: analyzer
```

### 3. Structure Your Prompts Clearly
```yaml
inputs:
  prompt: |
    Context: {{memory.user_prompt}}
    Previous Analysis: {{memory.market_analysis_output}}
    
    Task: Based on the context and analysis above, provide investment recommendations.
    
    Format: Provide 3-5 specific recommendations with rationale.
```

### 4. Handle Missing Memory Gracefully
The memory system handles missing variables by leaving them as empty strings, but you can design your prompts to be robust:

```yaml
inputs:
  prompt: |
    Question: {{memory.user_prompt}}
    {% if memory.previous_analysis_output %}
    Previous Analysis: {{memory.previous_analysis_output}}
    {% endif %}
    
    Provide a comprehensive answer.
```

## Advanced Features

### Custom Memory Classifications

You can save custom memory classifications in your tools:

```python
# In a custom tool
memory_manager.save_step_result("analysis", {
    "output": "Main analysis result",
    "classification": "analysis",
    "metadata": {"confidence": 0.95}
})

memory_manager.save_step_result("warning", {
    "output": "Low confidence in data source",
    "classification": "warning",
    "metadata": {"severity": "medium"}
})
```

Then access them in workflows:
```yaml
memory:
  needs: ["classification(analysis)", "classification(warning)"]
```

### Memory Debugging

Use the CLI to debug memory issues:

```bash
# View all memory for debugging
llm-cli workflow inspect --all

# Check recent execution details
llm-cli workflow inspect --recent
```

### Memory Cleanup

The memory system automatically manages storage, but you can clean up old entries:

```python
from app.memory_store import MemoryStore

store = MemoryStore()
# Remove entries older than 30 days
deleted_count = store.cleanup_old_entries(days_old=30)
```

## Error Handling

The memory system gracefully handles various error conditions:

- **Missing Variables**: Empty strings are substituted
- **Invalid Step Names**: Clear error messages with suggestions
- **Database Issues**: Automatic recovery and graceful degradation
- **Memory Overflow**: Efficient storage with automatic cleanup

## Performance Considerations

### Memory Efficiency
- Only requested memory is loaded into context
- SQLite provides efficient querying and storage
- Automatic indexing for fast retrieval

### Token Optimization
- Fractured context reduces unnecessary tokens
- Only relevant information is included in prompts
- Significant cost savings for long workflows

## Migration Guide

### From Traditional Workflows

If you have existing workflows without memory, you can gradually add memory support:

```yaml
# Before (no memory)
- name: step2
  tool: "model_call"
  inputs:
    prompt: "Continue the analysis..."

# After (with memory)
- name: step2
  tool: "model_call"
  memory:
    needs: ["tool_output(step1)"]
  inputs:
    prompt: "Continue the analysis from: {{memory.step1_output}}"
```

### Best Migration Practices
1. Start with simple memory patterns (`user_prompt`, `tool_output`)
2. Test each step to ensure memory variables resolve correctly
3. Use `llm-cli workflow inspect` to verify memory content
4. Gradually add more sophisticated memory patterns

## Troubleshooting

### Common Issues

#### Memory Variable Not Found
```
Error: Memory variable 'step_name_output' not found
```
**Solution**: Check step name spelling and ensure the step has completed

#### Empty Memory Content
```
Warning: Memory variable resolved to empty string
```
**Solution**: Verify the referenced step produced output and check memory needs

#### Database Locked
```
Error: Database is locked
```
**Solution**: Ensure no other workflow is running, restart if necessary

## Conclusion

The Fractured Context memory system transforms how AI workflows handle information, enabling:

- **Intelligent Context Management**: Steps get exactly what they need
- **Persistent Workflow Memory**: Complete execution history and analysis
- **Scalable Architecture**: Efficient storage and retrieval
- **Developer-Friendly**: Simple configuration, powerful capabilities

This system enables sophisticated multi-step AI reasoning while maintaining simplicity and efficiency. Your workflows can now build intelligent context awareness that rivals human-like reasoning patterns.

## Examples Repository

For more examples and advanced patterns, see:
- [`config.yaml`](../../config.yaml) - Working examples in the main configuration
- [`docs/TUTORIAL.md`](../TUTORIAL.md) - Custom tool development with memory integration
- [`scripts/test_memory_system.py`](../../scripts/test_memory_system.py) - Comprehensive testing examples

Happy workflow building! 🧠✨
