# Setting Up Lyra with Local LLM

This guide explains how to set up Lyra using local large language models (LLMs) for privacy and improved performance.

## Prerequisites

- **Windows 10/11** (for Linux, see the Linux setup section)
- **NVIDIA GPU** with at least 8GB VRAM (12GB+ recommended for larger models)
- **Git** installed for repository management
- **Python 3.10+** installed and in your PATH

## Quick Start Guide

1. Clone this repository:
```bash
git clone https://github.com/yourusername/Lyra.git
cd Lyra
```

2. Run the simple installation:
```bash
simple_install.bat
```

3. Set up the GPU-accelerated language model:
```bash
setup_cuda_llm.bat
```

4. Run the language model server:
```bash
run_gpu_llm.bat
```

5. In a separate terminal, run Lyra:
```bash
run_lyra.bat
```

## Key Files and Their Functions

### Configuration Files

- **`lyra_config.json`**: Main configuration file for all Lyra components including model paths and parameters
- **`secure_credentials.json`**: Contains API keys and authentication details (not committed to GitHub)

### Setup Scripts

- **`setup_env.bat`**: Sets up necessary environment variables for Lyra
- **`simple_install.bat`**: Installs core Python dependencies
- **`setup_cuda_llm.bat`**: Sets up CUDA and installs GPU-accelerated versions of required libraries

### Run Scripts

- **`run_gpu_llm.bat`**: Launches the language model server with GPU acceleration
- **`run_llama.bat`**: Alternative launcher for llama.cpp models
- **`run_lyra.bat`**: Launches the main Lyra application (connects to the language model server)

### Utility Scripts

- **`increase_pagefile.ps1`**: PowerShell script to increase Windows virtual memory (helpful for large models)
- **`fix_llama_android.bat`**: Fixes Android SDK errors in llama.cpp
- **`github_fix.bat`**: Resolves Git LFS issues for large file handling
- **`reset_github_repo.bat`**: Resets GitHub repository connection for a fresh start

### Repository Management

- **`.gitignore`**: Specifies intentionally untracked files to ignore
- **`.gitattributes`**: Sets attributes for paths in the repository, including LFS tracking
- **`.lfsconfig`**: Configuration for Git LFS (Large File Storage)

## Troubleshooting Common Issues

### GPU Memory Issues

If you encounter CUDA out-of-memory errors:

1. Try reducing the number of GPU layers in `run_gpu_llm.bat` (change `GPU_LAYERS=35` to a smaller number)
2. Run the `increase_pagefile.ps1` script as administrator to allocate more virtual memory
3. Use a smaller language model

### Git LFS Issues

If you encounter GitHub push errors with large files:

1. Ensure Git LFS is installed: `git lfs install`
2. Run the `github_fix.bat` script to fix LFS tracking issues
3. Make sure large binary files are properly tracked in `.gitattributes`

### Installation Problems

If installation fails:

1. Try running `clean_reinstall.bat` to perform a fresh installation
2. Ensure Python 3.10+ is properly installed and in your PATH
3. Check that you have the necessary Microsoft Visual C++ redistributables installed

## Model Selection and Configuration

Lyra supports multiple model types through the `lyra_config.json` file. The key parameters are:

- `model.path`: Path to your language model file (typically a .gguf file)
- `model.n_gpu_layers`: Number of layers to offload to GPU (adjust based on your GPU VRAM)
- `model.n_ctx`: Context window size (larger values require more memory)

Recommended starting point for a ~13B parameter model:
```json
{
  "model": {
    "path": "path/to/your/model.gguf",
    "n_gpu_layers": 35,
    "n_ctx": 4096
  }
}
```

## Advanced Configuration

For advanced users, Lyra offers extensive customization options:

- **Memory Systems**: Configure vector databases for long-term memory
- **Multi-modal Support**: Integrate image and video generation models
- **External Tools**: Connect to other AI tools and services

See the `lyra_config.json` file for all available options.

## Linux Setup

For Linux users:

1. Use the `setup_linux.sh` script instead of the .bat files
2. Ensure you have the necessary CUDA drivers installed for your GPU
3. Follow the same general workflow as described for Windows

## Getting Help

If you encounter issues not covered here, please:

1. Check the GitHub Issues page for similar problems and solutions
2. Run the troubleshooting scripts included in the repository
3. Open a new issue with detailed information about your setup and the problem

