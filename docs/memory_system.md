# Lyra Memory System Documentation

This document explains how Lyra's memory system works and how to use it effectively.

## Memory Architecture

Lyra uses a multi-layered memory architecture:

1. **Short-term memory**: Keeps track of the current conversation
2. **Working memory**: Maintains contextually relevant information
3. **Long-term memory**: Stores persistent information across sessions
4. **Episodic memory**: Remembers specific interactions and events

## Memory Components

### Combined Memory Manager

The `CombinedMemoryManager` orchestrates all memory components:

```python
from lyra.combined_memory_manager import CombinedMemoryManager

# Initialize with default settings
memory = CombinedMemoryManager()

# Store a new memory
memory.add("User likes chocolate ice cream", category="preferences")

# Retrieve relevant memories
relevant_memories = memory.retrieve("What dessert should I recommend?")
```

### SQLite Storage

Long-term memory is stored in an SQLite database:

- Location: `data/lyra.db`
- Tables: 
  - `memories`: Core memory storage
  - `memory_associations`: Links between related memories
  - `memory_metadata`: Additional memory attributes

### Vector Embeddings

Lyra uses vector embeddings to find semantically relevant memories:

- Embedding model: Sentence transformers
- Dimensions: 384 (default)
- Storage: Both in database and in memory for quick retrieval

## Memory Operations

### Storing Memories

```python
# Add a basic memory
memory_manager.add("Paris is the capital of France", category="facts")

# Add a memory with metadata
memory_manager.add(
    "User prefers dark mode",
    category="preferences",
    importance=0.8,
    source="user_settings"
)
```

### Retrieving Memories

```python
# Basic retrieval by relevance
memories = memory_manager.retrieve("What are some European capitals?")

# Filtered retrieval
memories = memory_manager.retrieve(
    "What are the user's interface preferences?",
    category="preferences",
    min_importance=0.7
)
```

### Forgetting and Updating

```python
# Update a memory
memory_manager.update(memory_id, "User now prefers light mode")

# Forget a memory
memory_manager.forget(memory_id)

# Reduce importance of old memories
memory_manager.decay(threshold_days=30, decay_factor=0.9)
```

## Memory Integration with LLMs

Lyra injects relevant memories into LLM prompts:

1. When a user query arrives, Lyra searches for relevant memories
2. The top N memories are formatted and added to the prompt
3. The LLM uses this context to generate more informed responses

## Advanced Memory Features

### Memory Reflection

Periodically, Lyra performs "memory reflection" to:
- Generate summaries of related memories
- Identify contradictions and update information
- Extract higher-level insights from multiple memories

### Memory Tags and Categories

Memories can be organized with:
- **Categories**: Broad groupings (facts, preferences, procedures)
- **Tags**: Specific labels for finer-grained retrieval

## Customizing Memory Behavior

Memory behavior can be customized via `config/memory_config.json`:

- `retention_period`: How long memories are kept
- `importance_threshold`: Minimum importance for memory retention
- `reflection_frequency`: How often memory reflection occurs
- `embedding_model`: Which model to use for embeddings
