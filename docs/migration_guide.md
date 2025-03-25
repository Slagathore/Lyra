# Migrating from OpenAI API to Local LLM Models

This guide will help you migrate your Lyra setup from using OpenAI's API to running with local LLM models.

## Steps to Migrate

### 1. Install Required Dependencies

First, install the necessary dependencies for running local models:

```bash
# Using the dependency resolver (recommended)
python resolve_dependencies.py --local-llm

# Or manually with pip
pip install llama-cpp-python transformers accelerate bitsandbytes torch
```

For GPU support on NVIDIA cards, ensure you have the CUDA toolkit installed (11.8+ recommended).

### 2. Download Models

Use the model manager to download appropriate models:

```bash
# List available models (if any)
python -m lyra.model_manager list

# Search for models on Hugging Face
python -m lyra.model_manager search "qwen quantized"

# Download a specific model
python -m lyra.model_manager download TheBloke/Qwen2.5-7B-GGUF --filename qwen2.5-7b.Q5_K_M.gguf

# Or download entire model repositories
python -m lyra.model_manager download TheBloke/Mistral-7B-Instruct-v0.2-GGUF
```

For best performance, we recommend:
- GGUF models for systems with less RAM (7B or 13B parameter models)
- Hugging Face models for systems with more RAM and GPU (larger models)

### 3. Update Configuration

The model manager will automatically set up your configuration, but you can manually configure:

```bash
# Set a specific model as default
python -m lyra.model_manager set-default path/to/your/model.gguf

# Or edit .env file to add:
LYRA_DEFAULT_MODEL=path/to/your/model.gguf
LYRA_MODEL_DIR=path/to/model/directory
```

### 4. Run with Local Models

Now you can run Lyra with your local models:

```bash
# Start Lyra normally - it will use local models by default
python -m lyra.main
```

You can also test your model before using it:

```bash
# Test model inference
python -m lyra.model_manager test path/to/your/model.gguf --prompt "Hello, who are you?"
```

## Hardware Requirements

Different models have different hardware requirements:

| Model Size | Minimum RAM | Recommended RAM | GPU Memory | Notes |
|------------|------------|-----------------|------------|-------|
| 7B (GGUF)  | 8 GB       | 16 GB           | 4+ GB      | Good for basic use |
| 13B (GGUF) | 16 GB      | 32 GB           | 8+ GB      | Better quality |
| 30B+ (GGUF)| 32 GB      | 64 GB           | 16+ GB     | High quality |
| 7B (HF)    | 16 GB      | 32 GB + GPU     | 8+ GB      | Better with GPU |
| 13B+ (HF)  | 32 GB      | 64 GB + GPU     | 16+ GB     | Requires GPU |

The implementation will automatically optimize based on your hardware:
- Auto-detection of GPU layers
- Dynamic context sizing based on available memory
- Automatic precision selection

## Troubleshooting

### Common Issues

1. **Out of memory errors**:
   - Try a smaller model
   - Use more quantized versions (Q4_K_M instead of Q6_K)
   - Reduce context size by setting environment variables: `LYRA_CONTEXT_SIZE=2048`

2. **Slow inference**:
   - Enable GPU acceleration if available
   - Try GGUF models which are optimized for CPU
   - Use smaller models if your hardware is limited

3. **Import errors**:
   - Ensure all dependencies are installed: `pip install -e ".[local-llm]"`
   - Check CUDA version compatibility with PyTorch

### Fallback to OpenAI

If you encounter issues with local models, you can temporarily revert to OpenAI:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Run Lyra with the OpenAI flag:
   ```bash
   python -m lyra.main --use_openai
   ```

## Advanced Configuration

### Memory Optimization

Tune memory usage with these environment variables:

```bash
# Set in .env file
LYRA_CONTEXT_SIZE=4096        # Maximum context window size
LYRA_GPU_LAYERS=-1            # Number of layers to offload to GPU (-1 for auto)
LYRA_QUANTIZATION=True        # Enable 8-bit quantization for Hugging Face models
```

### Model Management

The model manager provides several useful commands:

```bash
# Get detailed info about a model
python -m lyra.model_manager info path/to/model

# Delete a model to free space
python -m lyra.model_manager delete path/to/model

# Search for specific model types
python -m lyra.model_manager search "mistral instruct" --type text
```
