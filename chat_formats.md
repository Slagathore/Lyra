# Chat Formats in llama-cpp-python

## Overview

llama-cpp-python supports various chat formats that define how messages are formatted and sent to the model. Specifying the correct chat format is essential when working with models that were fine-tuned with specific templates.

## Common Chat Formats

Here are the most common chat formats supported by llama-cpp-python:

| Format | Description | For Models |
|--------|-------------|------------|
| `chatml` | OpenAI-style ChatML format | Qwen, OpenAI models, many modern models |
| `llama-2` | Format for Llama-2 chat models | Meta's Llama-2-chat models |
| `alpaca` | Format for Alpaca-style chat interactions | Alpaca, early instruction tuned models |
| `mistral` | Format for Mistral chat models | Mistral, Mixtral models |
| `vicuna` | Format for Vicuna-style interactions | Vicuna, early Llama-1 chat models |
| `falcon` | Format for Falcon models | Falcon chat models |
| `openchat` | Format for OpenChat models | OpenChat models |
| `chat-ml` | Alternative ChatML format | Some ChatML models |
| `zephyr` | Format for Zephyr models | Zephyr series models |

## Using Custom Chat Formats

You can set the chat format in two ways:

### 1. When Creating the Model

```python
model = llama_cpp.Llama(
    model_path="path/to/model.gguf",
    chat_format="chatml"  # Set chat format here
)
```

### 2. When Starting the Server

```bash
python -m llama_cpp.server --model "path/to/model.gguf" --chat_format chatml
```

## For Qwen Models

Qwen models (including Qwen2.5) typically use the `chatml` format. This format follows OpenAI's chat completion format with messages structured as:

