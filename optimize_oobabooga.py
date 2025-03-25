"""
Script to optimize oobabooga settings for your specific GPU
"""
import subprocess
import os
import re
import json
from pathlib import Path

# Constants
VRAM_RESERVE = 1.0  # Reserve 1GB of VRAM for system
MAX_THREADS = 12    # Maximum threads to use 
DEFAULT_BATCH = 512 # Default batch size
OOBABOOGA_DIR = Path("G:/AI/Lyra/oobabooga")
MODEL_PATH = Path("G:/AI/Lyra/BigModes/Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf/Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf")

def get_nvidia_info():
    """Get NVIDIA GPU information"""
    result = subprocess.run("nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader", 
                           shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error: Could not get GPU information. Make sure nvidia-smi is available.")
        return None

    lines = result.stdout.strip().split('\n')
    gpus = []
    
    for line in lines:
        parts = line.split(', ')
        if len(parts) >= 3:
            name = parts[0]
            memory = float(parts[1].split(' ')[0]) / 1024  # Convert to GB
            compute_cap = parts[2]
            
            gpus.append({
                'name': name,
                'memory': memory,
                'compute_capability': compute_cap
            })
    
    return gpus

def analyze_model_file(model_path):
    """Analyze the model file to get information"""
    if not model_path.exists():
        print(f"Error: Model file not found at {model_path}")
        return None
    
    size_gb = model_path.stat().st_size / (1024 * 1024 * 1024)
    
    # Extract model type from filename
    model_name = model_path.name
    quantization = "unknown"
    
    # Parse quantization from filename
    quant_patterns = ["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "Q2_K", "Q3_K_M", "Q4_0", "Q4_K_S", "Q5_K_S"]
    for pattern in quant_patterns:
        if pattern in model_name:
            quantization = pattern
            break
    
    return {
        'size_gb': size_gb,
        'quantization': quantization,
        'name': model_name
    }

def estimate_optimal_settings(gpu_info, model_info):
    """Estimate optimal settings for the model on this GPU"""
    if not gpu_info or not model_info:
        return None
    
    gpu = gpu_info[0]  # Use the first GPU
    
    # Estimate number of layers to offload based on VRAM and model size
    available_vram = gpu['memory'] - VRAM_RESERVE
    
    # Estimate optimal layers to offload to GPU
    # More aggressive for smaller quantized models
    if model_info['quantization'] in ["Q2_K", "Q3_K_M", "Q4_0", "Q4_K_S"]:
        # These quantizations are very efficient
        gpu_layers = 100  # Try to put all layers on GPU
    elif model_info['quantization'] in ["Q4_K_M", "Q5_K_S"]:
        # Medium efficiency
        gpu_layers = int(min(100, available_vram * 6.5))
    elif model_info['quantization'] in ["Q5_K_M", "Q6_K"]:
        # Less efficient
        gpu_layers = int(min(100, available_vram * 5))
    else:
        # Q8_0 or unknown - be conservative
        gpu_layers = int(min(100, available_vram * 4))
    
    # Adjust batch size based on available VRAM
    batch_size = DEFAULT_BATCH
    if available_vram < 6:
        batch_size = 256
    elif available_vram > 20:
        batch_size = 1024
    
    # Determine if we should use tensor cores
    use_tensor_cores = gpu['name'].lower().find('rtx') >= 0
    
    # CPU threads - based on system info but capped
    cpu_count = os.cpu_count() or 8
    threads = min(MAX_THREADS, max(4, cpu_count - 2))
    
    # Context size - typical value of 4096 works well
    context_size = 4096
    
    return {
        'gpu_layers': gpu_layers,
        'batch_size': batch_size,
        'use_tensor_cores': use_tensor_cores,
        'threads': threads,
        'context_size': context_size,
        'no_offload_kqv': True  # This generally improves performance with high gpu_layers
    }

def create_optimized_script(settings, model_path):
    """Create an optimized script for running oobabooga"""
    script_path = OOBABOOGA_DIR / "run_optimized_gpu.bat"
    model_path_str = str(model_path).replace('\\', '\\\\')
    
    tensor_cores_param = "--tensorcores" if settings['use_tensor_cores'] else ""
    
    with open(script_path, 'w') as f:
        f.write('@echo off\n')
        f.write('echo Running optimized GPU configuration for your model...\n\n')
        
        # Set proper CUDA environment
        f.write(':: Set proper CUDA environment\n')
        f.write('set "CUDA_PATH=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.1"\n')
        f.write('set "CUDA_HOME=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.1"\n')
        f.write('set "PATH=%PATH%;C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.1\\bin"\n\n')
        
        # Activate conda
        f.write('call "%UserProfile%\\miniconda3\\Scripts\\activate.bat"\n\n')
        
        # Launch command with optimized settings
        f.write(':: Run with GPU optimized parameters\n')
        cmd = f'python server.py --model "{model_path_str}" --loader llama.cpp --n-gpu-layers {settings["gpu_layers"]} '
        cmd += f'--threads {settings["threads"]} --n_batch {settings["batch_size"]} --n-ctx {settings["context_size"]} '
        cmd += f'{tensor_cores_param} {"--no_offload_kqv" if settings["no_offload_kqv"] else ""} --api --verbose'
        
        f.write(f'{cmd}\n')
    
    # Create a supporting markdown file with explanations
    doc_path = OOBABOOGA_DIR / "gpu_optimization_notes.md"
    with open(doc_path, 'w') as f:
        f.write(f'# GPU Optimization for {model_path.name}\n\n')
        f.write('## Recommended Settings\n\n')
        f.write(f'- **GPU Layers:** {settings["gpu_layers"]}\n')
        f.write(f'- **Batch Size:** {settings["batch_size"]}\n')
        f.write(f'- **Context Size:** {settings["context_size"]}\n')
        f.write(f'- **Threads:** {settings["threads"]}\n')
        f.write(f'- **Tensor Cores:** {"Enabled" if settings["use_tensor_cores"] else "Disabled"}\n')
        f.write(f'- **KQV Offloading:** {"Disabled for better performance" if settings["no_offload_kqv"] else "Enabled"}\n\n')
        
        f.write('## Explanation\n\n')
        f.write('- **GPU Layers:** Number of layers to offload to your GPU. Higher means more GPU usage but faster inference.\n')
        f.write('- **Batch Size:** How many tokens to process at once. Higher values use more memory but can be faster.\n')
        f.write('- **Context Size:** Maximum context window. 4096 is a good balance between memory usage and capability.\n')
        f.write('- **Threads:** CPU threads used for processing. Usually set close to your core count.\n')
        f.write('- **No KQV Offload:** When enabled, KQV matrices stay in GPU memory, improving performance but using more VRAM.\n\n')
        
        f.write('## Adjustments\n\n')
        f.write('If you experience out-of-memory errors:\n')
        f.write('1. Reduce `--n-gpu-layers` value\n')
        f.write('2. Remove the `--no_offload_kqv` parameter\n')
        f.write('3. Reduce `--n-ctx` value\n\n')
        
        f.write('If you want better performance and have extra VRAM:\n')
        f.write('1. Increase `--n-gpu-layers`\n')
        f.write('2. Add `--no_offload_kqv` if not already present\n')
    
    return script_path, doc_path

def main():
    print("Analyzing your GPU and model to optimize settings...")
    
    # Get GPU information
    gpu_info = get_nvidia_info()
    if not gpu_info:
        print("Could not get GPU information. Cannot continue.")
        return
    
    print(f"Detected GPU: {gpu_info[0]['name']} with {gpu_info[0]['memory']:.1f}GB VRAM")
    
    # Analyze model
    model_info = analyze_model_file(MODEL_PATH)
    if not model_info:
        print("Could not analyze model file. Cannot continue.")
        return
    
    print(f"Model: {model_info['name']}")
    print(f"Size: {model_info['size_gb']:.2f}GB")
    print(f"Quantization: {model_info['quantization']}")
    
    # Calculate optimal settings
    settings = estimate_optimal_settings(gpu_info, model_info)
    if not settings:
        print("Could not calculate optimal settings.")
        return
    
    print("\nRecommended Settings:")
    print(f"GPU Layers: {settings['gpu_layers']}")
    print(f"Batch Size: {settings['batch_size']}")
    print(f"Tensor Cores: {'Enabled' if settings['use_tensor_cores'] else 'Disabled'}")
    print(f"Threads: {settings['threads']}")
    print(f"Context Size: {settings['context_size']}")
    print(f"No KQV Offload: {settings['no_offload_kqv']}")
    
    # Create optimized script
    script_path, doc_path = create_optimized_script(settings, MODEL_PATH)
    
    print(f"\nCreated optimized script: {script_path}")
    print(f"Created documentation: {doc_path}")
    print("\nYou can now run the script to start oobabooga with optimized settings.")

if __name__ == "__main__":
    main()
