# Troubleshooting Lyra's Self-Improvement System

This guide helps you troubleshoot common issues with Lyra's self-improvement components and LLM integrations.

## Table of Contents
- [Common Error Messages](#common-error-messages)
- [LLM API Connection Issues](#llm-api-connection-issues)
- [Self-Improvement Module Issues](#self-improvement-module-issues)
- [Batch Script Failures](#batch-script-failures)
- [Logging and Diagnostics](#logging-and-diagnostics)

## Common Error Messages

### "No LLM providers are enabled"
This means no LLM provider is properly configured for code analysis. Run:
```batch
configure_llm_advisors.bat
```
And enable at least one provider (local is enabled by default).

### "Local LLM request failed"
This usually means the local LLM server isn't running. Start it with:
```batch
run_gpu_llm_fixed.bat
```

### "API key not configured"
You need to set up API keys for external providers:
```batch
configure_llm_advisors.bat
```
Then choose the provider to configure.

### "Error getting LLM suggestions"
This could be due to:
- Network connectivity issues
- Invalid API keys
- Rate limiting
- Server errors

Try running:
```batch
llm_advisor_cli.bat test --provider [provider_name]
```

## LLM API Connection Issues

### Testing API Connections

Use the test command to check each provider:
```batch
llm_advisor_cli.bat test --provider openai
llm_advisor_cli.bat test --provider deepseek
llm_advisor_cli.bat test --provider anthropic
llm_advisor_cli.bat test --provider local
```

### Local LLM Issues

1. Check if the server is running:
   ```batch
   curl http://127.0.0.1:8000/health
   ```

2. If not running, start it:
   ```batch
   run_gpu_llm_fixed.bat
   ```

3. If that fails, try the alternative server:
   ```batch
   alternative_gpu_llm.bat
   ```

4. Check GPU status:
   ```batch
   check_cuda_install.bat
   ```

### External API Issues

1. Verify your API key is correct in `data/advisor_config.json`
2. Check your account balance/quota at the provider's website
3. Verify network connectivity to the API endpoint

## Self-Improvement Module Issues

### Module Not Found

If you see `ImportError` or "module not found" errors:

1. Run the setup script:
   ```batch
   self_improvement.bat
   ```

2. Check if modules were created:
   ```batch
   test_integrations.bat
   ```

3. Check if all required packages are installed:
   ```batch
   pip install GitPython autopep8 pylint pytest requests
   ```

### Integration Test Failures

Run the self-improvement tests:
```batch
python -m unittest tests/test_self_improvement.py
```

## Batch Script Failures

### Common Issues

1. **Environment Activation Fails**: Make sure you have a valid Python environment at `lyra_env`.
   ```batch
   python -m venv lyra_env
   lyra_env\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. **File Not Found Errors**: Make sure all paths are correct:
   ```batch
   verify_model_path.bat
   ```

3. **Command Not Found**: Make sure all dependencies are installed:
   ```batch
   setup_everything.bat
   ```

## Logging and Diagnostics

### Finding Log Files

Log files are stored in the `logs` directory:
- `logs/self_improvement_errors.log` - Self-improvement specific errors
- `logs/llm_advisor.log` - LLM API interaction logs

### Running System Health Check

```batch 
check_system_health.bat
```

### Debug Mode

Run Lyra in debug mode to get more detailed logs:
```batch 
python launch_lyra.py --debug --with-self-improvement
```

## Getting Help

If you continue to experience issues:

1. Check the GitHub issues: https://github.com/yourusername/lyra/issues
2. Run the collection feedback tool to report the issue:
   ```batch
   collect_feedback.bat
   ```
