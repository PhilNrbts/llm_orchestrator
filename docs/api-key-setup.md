# API Key Setup Guide

The LLM Orchestrator supports multiple ways to manage your API keys securely. Choose the method that works best for your workflow.

## 🔐 Option 1: Encrypted Vault (Recommended for Production)

The most secure option - stores all API keys in an encrypted file.

### Setup
```bash
# Create the encrypted vault
python scripts/init_vault.py

# Use the interactive setup
python scripts/setup_env.py
```

### Usage
```bash
# Load keys and run a workflow
python scripts/load_env_keys.py python scripts/run_workflow.py sequential_elaboration user_prompt="test"

# Export keys to your shell
eval $(python scripts/load_env_keys.py --export)
```

## 🌍 Option 2: Environment Variables (Development)

Set API keys directly in your environment - convenient for development.

### Manual Setup
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
export MISTRAL_API_KEY="your-mistral-key"
```

### Interactive Setup
```bash
python scripts/setup_env.py
```

### Permanent Setup (add to ~/.bashrc or ~/.zshrc)
```bash
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
# ... etc
```

## 🚀 Option 3: Programmatic (Python Code)

Pass the vault password directly when creating the workflow engine.

```python
from app.workflow_engine import WorkflowEngine

# With vault password
engine = WorkflowEngine(vault_password="your-vault-password")
result = engine.run("sequential_elaboration", {"user_prompt": "test"})

# Without password (uses environment variables)
engine = WorkflowEngine()
result = engine.run("sequential_elaboration", {"user_prompt": "test"})
```

## 🔄 How It Works

The system checks for API keys in this order:

1. **Vault password provided** → Decrypt vault.enc and use those keys
2. **Environment variables** → Use keys from ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.
3. **No keys found** → Fall back to simulation mode

## 🧪 Testing Your Setup

After setting up your API keys, test with:

```bash
# Quick test
python scripts/run_workflow.py sequential_elaboration user_prompt="Hello world"

# Full test suite
python scripts/test_real_tools.py
```

## 🛡️ Security Notes

- **Vault method**: Keys are encrypted at rest, password never stored
- **Environment method**: Keys visible in process environment
- **Never commit API keys** to version control
- **Use .env files** for local development (add to .gitignore)

## 🔧 Troubleshooting

### "No API keys found"
- Check if vault.enc exists: `ls -la vault.enc`
- Check environment variables: `env | grep API_KEY`
- Run setup: `python scripts/setup_env.py`

### "Invalid vault password"
- Double-check your password
- Recreate vault if forgotten: `python scripts/init_vault.py`

### "API call failed"
- Verify your API keys are valid
- Check your internet connection
- Review provider-specific error messages

## 📋 Quick Reference

| Task | Command |
|------|---------|
| Create vault | `python scripts/init_vault.py` |
| Interactive setup | `python scripts/setup_env.py` |
| Load keys and run | `python scripts/load_env_keys.py <command>` |
| Export to shell | `eval $(python scripts/load_env_keys.py --export)` |
| Run workflow | `python scripts/run_workflow.py <workflow> <params>` |
| Test setup | `python scripts/test_real_tools.py` |

Choose the method that fits your security requirements and workflow preferences!
