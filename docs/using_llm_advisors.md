# Using External LLM Advisors with Lyra

This guide explains how to use DeepSeek, OpenAI, and other LLMs to get code improvement suggestions for your Lyra codebase.

## Table of Contents
- [Overview](#overview)
- [Setting Up LLM Advisors](#setting-up-llm-advisors)
- [Command Line Usage](#command-line-usage)
- [Python API Usage](#python-api-usage)
- [Comparing Multiple LLMs](#comparing-multiple-llms)
- [Using with Vintix RL](#using-with-vintix-rl)

## Overview

Lyra's LLM Advisor system allows you to leverage powerful external language models to:

1. Get code improvement suggestions
2. Find potential bugs
3. Optimize algorithms
4. Compare suggestions from multiple different LLMs

The system supports:
- DeepSeek (specialized in code analysis)
- OpenAI (GPT-4 and other models)
- Claude/Anthropic
- Local LLMs (via API server)

## Setting Up LLM Advisors

### Initial Setup

1. First ensure your self-improvement module is set up:
   ```batch
   self_improvement.bat
   ```

2. Configure your LLM providers using the configuration tool:
   ```batch
   configure_llm_advisors.bat
   ```

3. For a quick DeepSeek setup:
   ```batch
   setup_deepseek.bat
   ```

### API Keys

You'll need to obtain API keys from the services you want to use:
- DeepSeek: https://platform.deepseek.com/api-keys
- OpenAI: https://platform.openai.com/api-keys 
- Anthropic: https://console.anthropic.com/keys

## Command Line Usage

The `llm_advisor_cli.bat` tool provides easy access to LLM analysis:

### Getting Code Improvement Suggestions

```batch
llm_advisor_cli.bat analyze --file src/lyra/main.py --provider deepseek
```

Options:
- `--provider`: Choose the LLM provider (deepseek, openai, anthropic, local)
- `--type`: Analysis type (code_review, bug_fixing, algorithm_optimization)

### Comparing Multiple Providers

```batch
llm_advisor_cli.bat compare --file src/lyra/main.py --providers "deepseek,openai"
```

### Testing Connections

```batch
llm_advisor_cli.bat test --provider deepseek
```

## Python API Usage

You can integrate LLM advisors directly into your Python code:

```python
from lyra.self_improvement.llm_advisor import LLMAdvisor

# Initialize the advisor
advisor = LLMAdvisor()

# Get code improvement suggestions
with open('path/to/code.py', 'r') as f:
    code = f.read()

# Basic usage
result = advisor.get_advice(code, file_path='path/to/code.py')

# Using specific provider and analysis type
result = advisor.get_advice(code, 
                           file_path='path/to/code.py',
                           provider='deepseek',
                           prompt_type='bug_fixing')

# Process results
if result['success']:
    print(f"Got {len(result['suggestions'])} suggestions:")
    for suggestion in result['suggestions']:
        print(f"- {suggestion['type']}: {suggestion['text'][:100]}...")
else:
    print(f"Error: {result['error']}")
```

## Comparing Multiple LLMs

```python
from lyra.self_improvement.llm_advisor import compare_suggestions

with open('path/to/code.py', 'r') as f:
    code = f.read()

# Compare DeepSeek and local LLM
results = compare_suggestions(code, providers=['deepseek', 'local'])

# Access individual provider results
deepseek_results = results['provider_results']['deepseek']
local_results = results['provider_results']['local']

# Access combined suggestions
all_suggestions = results['combined']['all_suggestions']
```

## Using with Vintix RL

The LLM advisors integrate with Lyra's reinforcement learning system:

```batch
vintix_cli.bat advisor --file src/lyra/main.py --provider deepseek
```

Or from Python:

```python
from lyra.self_improvement.reinforcement_learning import VintixRL

rl = VintixRL()

with open('path/to/code.py', 'r') as f:
    code = f.read()

# Get suggestions from the default provider
suggestions = rl.get_improvement_suggestions(code, context={"file_path": "path/to/code.py"})

# Get expert advice from multiple providers
expert_advice = rl.get_expert_advice(code, file_path="path/to/code.py")
```

## Advanced Configuration

The advisor configuration is stored in `data/advisor_config.json`. You can modify:

- API endpoints
- Default models
- Prompt templates
- Temperature settings

For deeper customization, you can edit the configuration file directly or modify the prompts for specialized analysis.
