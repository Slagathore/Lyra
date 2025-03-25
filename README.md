# Lyra - Multi-Model LLM Management

This system allows you to easily manage and switch between multiple language models.

## Key Features

- **Natural Language Processing**: Communicate naturally with Lyra using everyday language
- **Memory Management**: Lyra remembers past conversations and learns from interactions
- **Self-Improvement**: The system can analyze and improve its own code
- **LLM Integration**: Uses state-of-the-art language models for intelligent responses
- **GPU Acceleration**: Optimized for NVIDIA GPUs to run efficiently

## Quick Start

1. **Setup Everything**:
   ```batch
   setup_everything.bat
   ```

2. **List available models:**
   ```
   list_models.bat
   ```

3. **Select a model to use:**
   ```
   python select_model.py MODEL_NAME
   ```

4. **Run the selected model:**
   ```
   run_active_model.bat
   ```

5. **Start an API server with the selected model:**
   ```
   run_api_server.bat
   ```

## System Requirements

- Windows 10/11
- Python 3.8 or newer
- NVIDIA GPU with 8GB+ VRAM (recommended)
- CUDA 11.8+ (for GPU acceleration)

## Components

- **LLM Server**: Runs the large language model for text generation
- **Memory System**: Manages conversation history and learned information
- **Self-Improvement Module**: Allows Lyra to analyze and improve its own code
- **LLM Advisor Integration**: Leverages external LLMs like DeepSeek for code analysis

## Available Commands

- `list_models.bat` - Display all available models and scan for new ones
- `select_model.py` - Select which model to use
- `run_active_model.bat` - Run the currently selected model in chat mode
- `run_api_server.bat` - Start an OpenAI-compatible API server with the active model

## Adding New Models

The system will automatically scan for new GGUF model files in the `G:/AI/Lyra/BigModes` directory and its subdirectories. You can simply place new model files in this directory, then run `list_models.bat` to detect them.

## Model Configuration

Model settings are stored in `model_config.json`. This file is managed automatically but can be edited manually if needed.

Each model has these configurable properties:
- `name`: Display name for the model
- `path`: Path to the model file
- `type`: Model type (e.g., "llama-cpp")
- `chat_format`: Format for chat prompts (e.g., "chatml", "llama-2", "mistral")
- `n_gpu_layers`: Number of layers to offload to GPU
- `n_ctx`: Context window size
- `n_batch`: Batch size for inference
- `active`: Whether this is the currently active model
- `description`: Optional description

## Using the API Server

When running `run_api_server.bat`, an OpenAI-compatible REST API will be available at http://localhost:8000/v1.

Example Python code to use the API:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # any value works
)

response = client.chat.completions.create(
    model="any-model-name",  # model name doesn't matter for the server
    messages=[
        {"role": "user", "content": "Write a short poem about AI."}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

## Troubleshooting

If you encounter any issues:

1. Run `check_system_health.bat` for a comprehensive system check
2. See `docs/troubleshooting.md` for common problems and solutions
3. Run `fix_llm_errors.bat` to resolve LLM-related issues
4. Run `fix_self_improvement.bat` to fix self-improvement module issues

If a model fails to load, try:

1. Check if your llama-cpp-python version supports the model architecture
2. Update llama-cpp-python: `pip install --upgrade llama-cpp-python`
3. Try using a pre-built CUDA wheel: `pip install --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python`
4. Reduce the number of GPU layers (n_gpu_layers) in the model configuration

## Advanced Usage

For advanced usage and development, see the documentation in the `docs` directory.

