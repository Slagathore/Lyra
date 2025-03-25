import logging
import os
import markdown
import json

logger = logging.getLogger(__name__)

class Documentation:
    def __init__(self, docs_dir=None):
        if docs_dir is None:
            # Use the docs directory in the Lyra root
            self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
        else:
            self.docs_dir = docs_dir
            
        # Create docs directory if it doesn't exist
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Initialize with some default docs if not present
        self._initialize_default_docs()
        
    def _initialize_default_docs(self):
        default_docs = {
            "getting_started.md": self._get_getting_started_content(),
            "model_settings.md": self._get_model_settings_content(),
            "chat_settings.md": self._get_chat_settings_content(),
            "memory_management.md": self._get_memory_management_content(),
            "generation_features.md": self._get_generation_features_content(),
            "troubleshooting.md": self._get_troubleshooting_content()
        }
        
        for filename, content in default_docs.items():
            file_path = os.path.join(self.docs_dir, filename)
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Created default documentation file: {filename}")
                except Exception as e:
                    logger.error(f"Error creating documentation file {filename}: {str(e)}")
    
    def get_document(self, doc_name):
        """Get the content of a documentation file by name"""
        try:
            file_path = os.path.join(self.docs_dir, f"{doc_name}.md")
            if not os.path.exists(file_path):
                return f"Documentation for '{doc_name}' not found."
                
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Convert markdown to HTML
            html_content = markdown.markdown(content)
            return html_content
        except Exception as e:
            logger.error(f"Error getting document {doc_name}: {str(e)}")
            return f"Error retrieving documentation: {str(e)}"
    
    def get_document_list(self):
        """Get a list of all available documentation files"""
        try:
            doc_files = [f.replace(".md", "") for f in os.listdir(self.docs_dir) if f.endswith(".md")]
            return doc_files
        except Exception as e:
            logger.error(f"Error getting document list: {str(e)}")
            return []
    
    def _get_getting_started_content(self):
        return """# Getting Started with Lyra

## Introduction
Lyra is an AI assistant interface designed to help you interact with various AI models and generation capabilities.

## Quick Start
1. **Choose a Model**: Select an AI model from the dropdown in the Models tab
2. **Adjust Settings**: Configure the model parameters for optimal performance
3. **Start Chatting**: Go to the Chat tab and start a conversation
4. **Use Advanced Features**: Explore image generation, text-to-speech, and code generation

## System Requirements
- Python 3.8 or higher
- Recommended: NVIDIA GPU with at least 8GB VRAM for larger models
- At least 16GB of system RAM

## Troubleshooting
If you encounter issues, please check the Troubleshooting guide or review the server logs for detailed error messages.
"""

    def _get_model_settings_content(self):
        return """# Model Settings Guide

## Loading Models
1. Navigate to the Models tab
2. Select a model from the dropdown menu
3. Adjust settings appropriate for your hardware
4. Click "Load Model" to initialize

## Important Settings
- **GPU Layers**: Number of layers to offload to GPU (0 for CPU only)
- **Context Size**: Maximum conversation history (in tokens)
- **n_batch**: Batch size for processing (higher = faster but more memory)
- **threads**: CPU threads to use (adjust based on your system)

## Advanced Settings
- **LoRA**: Path to LoRA adapter if you want to use one
- **RoPE Scaling**: Adjusts position embeddings for extended context
- **Chat Template**: Format for structuring conversation exchanges

## Recommended Configurations
### Low-end system (8GB RAM, no GPU)
- Small models only (7B parameters or less)
- GPU Layers: 0
- Context Size: 2048
- n_batch: 512

### Mid-range system (16GB RAM, 8GB VRAM)
- Medium models (up to 13B parameters)
- GPU Layers: 32
- Context Size: 4096
- n_batch: 512

### High-end system (32GB+ RAM, 24GB+ VRAM)
- Large models (up to 70B parameters)
- GPU Layers: All layers
- Context Size: 8192+
- n_batch: 1024
"""

    def _get_chat_settings_content(self):
        return """# Chat Settings Guide

## Conversation Management
- **New Chat**: Starts a fresh conversation
- **Clear Chat**: Removes all messages but keeps settings
- **Save/Load Chat**: Export and import conversations

## Personality Settings
- **System Prompt**: Sets the AI's behavior and role
- **Temperature**: Controls randomness (0.1-2.0)
- **Top P**: Controls diversity of responses (0.0-1.0)
- **Repetition Penalty**: Reduces repetitive outputs

## Preset Personalities
The personality presets provide quick access to different AI roles:
- **Creative Assistant**: Higher temperature for more creative responses
- **Professional Helper**: Balanced settings for work-related tasks
- **Code Assistant**: Optimized for programming help
- **Concise Responder**: Provides brief, direct answers

## Memory Management
- Chat history is automatically managed to stay within the model's context window
- You can pin important messages to prevent them from being forgotten
- System prompts are always preserved in memory
"""

    def _get_memory_management_content(self):
        return """# Memory Management

## How Chat Memory Works
Lyra maintains a conversation history that serves as context for the AI model. This memory has limitations based on the model's maximum context size (measured in tokens).

## Token Management
- Each character roughly corresponds to 0.25-0.5 tokens
- The system automatically removes older messages when approaching the token limit
- System messages are preserved to maintain the AI's personality

## Advanced Memory Features
- **Pin Message**: Keep important messages in context
- **Summarize History**: Condense lengthy conversations
- **Memory Visualization**: See token usage in the Memory tab

## Tips for Effective Memory Use
1. Keep system prompts concise but informative
2. Use clear, direct language to reduce token usage
3. Start a new chat for completely different topics
4. For code generation, focus queries on specific functions rather than entire applications
"""

    def _get_generation_features_content(self):
        return """# Generation Features Guide

## Text Generation
- **Chat**: Interactive conversation with the AI
- **Completion**: Generate text from a single prompt without chat history

## Image Generation
Lyra supports generating images from text descriptions:
1. Go to the Images tab
2. Enter a detailed description of the desired image
3. Adjust settings like size and steps
4. Click "Generate"

## Text-to-Speech
Convert text to spoken audio:
1. Select the TTS tab
2. Enter or paste text
3. Choose a voice and adjust speed
4. Click "Generate Speech"

## Code Generation
Get programming help:
1. Navigate to the Code tab
2. Describe the code you need
3. Select the programming language
4. Get generated code you can copy and use

## Troubleshooting Generation
- If image generation produces black images, check model installation
- For TTS issues, ensure required libraries are installed
- If code generation is incomplete, try breaking down the request into smaller parts
"""

    def _get_troubleshooting_content(self):
        return """# Troubleshooting Guide

## Common Issues and Solutions

### Model Loading Problems
- **Error: "CUDA out of memory"**: Reduce GPU layers or switch to a smaller model
- **Slow loading**: Check disk speed or increase threads parameter
- **Model not found**: Verify the model path is correct

### Chat Errors
- **Max tokens error**: Your context window is full. Start a new chat or clear history
- **Incomplete responses**: Adjust max_new_tokens setting higher
- **Model not loaded error**: Go to Models tab and load a model before chatting

### Image Generation Issues
- **Black images**: Ensure stable-diffusion dependencies are installed
- **CUDA errors**: Try reducing the image size or steps
- **Missing models**: Install required model checkpoints

### Text-to-Speech Problems
- **No audio output**: Check that required TTS libraries are installed
- **Language errors**: Verify the selected voice supports your text language

### Public Sharing Errors
- **Missing arguments error**: Configure sharing settings in the config file
- **Connection issues**: Check your internet connection and firewall settings

## Checking Logs
Server logs contain detailed error information that can help diagnose problems:
1. Check the terminal/console where Lyra is running
2. Look for error messages with timestamps
3. Report issues with the full error message for better support

## Getting Help
If you can't resolve an issue, collect the following information:
- Full error message from logs
- Your system specifications
- Steps to reproduce the problem
"""

# Function to get documentation instance
_docs_instance = None

def get_documentation():
    global _docs_instance
    if _docs_instance is None:
        _docs_instance = Documentation()
    return _docs_instance
