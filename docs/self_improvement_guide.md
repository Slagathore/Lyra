# Lyra Self-Improvement System Guide

This comprehensive guide explains how Lyra's self-improvement system works and how to use it effectively.

## Overview

Lyra's self-improvement system allows the AI to analyze and modify its own codebase, learn from past changes, and continuously enhance its capabilities. This system consists of several interconnected components:

- **Code Manager**: Analyzes and modifies the codebase
- **Vintix RL**: Reinforcement learning system that learns from feedback
- **LLM Advisor**: Gets code improvement suggestions from external LLMs
- **GitHub Integration**: Interfaces with GitHub repositories
- **Implementation Runner**: Tests and deploys code changes safely

## Setting Up Self-Improvement

To initialize the self-improvement system:

```batch
self_improvement.bat
```

For optimal results, also set up external LLM advisors:

```batch
setup_deepseek.bat
configure_llm_advisors.bat
```

## Using the Vintix CLI

The Vintix CLI provides access to self-improvement features:

```batch
vintix_cli.bat learn record --file src/lyra/main.py --desc "Added logging"
vintix_cli.bat improve --file src/lyra/main.py
vintix_cli.bat status
vintix_cli.bat advisor --file src/lyra/main.py --provider deepseek
```

## Using LLM Advisors

LLM advisors provide code improvement suggestions:

```batch
llm_advisor_cli.bat analyze --file src/lyra/main.py --provider deepseek
llm_advisor_cli.bat compare --file src/lyra/main.py --providers "local,deepseek"
```

See `docs/using_llm_advisors.md` for detailed information.

## Self-Improvement Workflow

A typical self-improvement workflow:

1. **Identify**: Find code that could be improved
2. **Analyze**: Use LLM advisors to get suggestions
3. **Implement**: Test and implement changes
4. **Learn**: Record feedback on those changes

## Reinforcement Learning

The Vintix RL system learns from code changes and feedback:

- **Experience Data**: Stored in `data/vintix_rl/experience.json`
- **Learning Process**: Analyzes patterns in successful changes
- **Suggestions**: Provides improvement recommendations based on past experience

## GitHub Integration

To set up GitHub integration for version control:

```batch
setup_github.bat
```

Then use the GitHub commands:

```batch
vintix_cli.bat github push --message "Automated improvements"
vintix_cli.bat github pr --title "Feature update" --body "Implements new feature"
```

## Advanced Configuration

Advanced configuration options are available for the self-improvement system:

- Edit advisor configuration: `data/advisor_config.json`
- Modify RL parameters: `data/vintix_rl/config.json`
- Customize test parameters: `tests/config.json`

## Troubleshooting

If you encounter issues with the self-improvement system:

1. Run `diagnose_llm_connections.bat` to check LLM connectivity
2. Run `fix_self_improvement.bat` to repair common issues
3. See `docs/troubleshooting.md` for detailed solutions
