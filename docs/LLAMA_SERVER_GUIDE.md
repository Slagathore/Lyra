# Using llama-server with Lyra

This guide explains how to use the `llama-server` approach for serving models in Lyra, which provides a much simpler and more efficient way to load and use LLM models.

## What is llama-server?

`llama-server` is part of the llama.cpp project and provides an OpenAI-compatible API server for serving LLM models.
It's lightweight, efficient, and much easier to use than building custom Python bindings.

Benefits include:

- OpenAI-compatible API
- Built-in web UI for testing
- Support for multiple models
- Parallel request handling
- Grammar-constrained outputs
- Streaming responses

## Installation

You need to have the `llama-server` executable available on your system. There are several ways to get it:

### Option 1: Use a pre-built binary

Download a pre-built binary from the llama.cpp releases page:
<https://github.com/ggerganov/llama.cpp/releases>

### Option 2: Build from source

```bash
# Clone the repository
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Build the server
make

# The executable will be in the build directory
```

### Option 3: Install via Python package

```bash
pip install llama-cpp-python[server]
```

## Using the Launcher Script

Lyra includes a launcher script that makes it easy to start a llama-server with your models:

```bash
# List available models
python scripts/launch_llama_server.py --list-models

# Start server with a specific model
python scripts/launch_llama_server.py --model "Your Model Name"

# Start server with custom options
python scripts/launch_llama_server.py --model "Your Model Name" --port 8080 --n-parallel 4
```

### Command-line Options

- `--model`, `-m`: Name of the model to use (must be in your Lyra config)
- `--port`, `-p`: Port for the server (default: 8080)
- `--list-models`, `-l`: List available models
- `--n-gpu-layers`: Override the number of GPU layers to use
- `--n-parallel`, `-np`: Number of parallel inference requests (default: 1)
- `--n-threads`, `-t`: Number of threads (0=auto)
- `--grammar-file`, `-g`: Path to a grammar file

## Using with Lyra

Lyra can connect to the llama-server in two ways:

### 1. Automatic Mode

Just configure your model to use the server provider:

```json
{
  "model_name": "Your Model",
  "model_path": "/path/to/model.gguf",
  "model_type": "llama",
  "auto_start_server": true,
  "host": "127.0.0.1",
  "port": 8080
}
```

With `auto_start_server` set to `true`, Lyra will automatically start the server when needed.

### 2. Manual Mode

Start the server separately:

```bash
python scripts/launch_llama_server.py --model "Your Model Name"
```

Then configure your model to connect to it:

```json
{
  "model_name": "Your Model",
  "model_path": "/path/to/model.gguf",
  "model_type": "llama",
  "auto_start_server": false,
  "host": "127.0.0.1",
  "port": 8080
}
```

## Web UI

The llama-server includes a basic web UI that you can access at:

## Llama Server Guide

This guide explains how to use the Llama server with Lyra.

### Setup Steps

1. Install the required dependencies
2. Configure the server settings
3. Launch the server
4. Connect Lyra to the running server

### Server Configuration

The server can be accessed at <http://localhost:8000> when running locally.

### Troubleshooting

If you encounter issues with the server, check the following:

- Ensure all dependencies are installed
- Verify port 8000 is not in use by another application
- Check the logs for specific error messages
