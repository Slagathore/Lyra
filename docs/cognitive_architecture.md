# Lyra's Cognitive Architecture

## Overview

Lyra's cognitive architecture is designed to provide a more human-like and contextually aware experience by integrating several specialized cognitive components. This document outlines the primary components and how they interact.

## Core Cognitive Components

### 1. Cognitive Integration

**Purpose**: Acts as the central coordinator for all cognitive components, ensuring they work together cohesively.

**File**: `modules/cognitive_integration.py`

**Key Functions**:

- Loading and initializing all cognitive components
- Processing user messages through appropriate components
- Determining when to trigger reflections
- Storing interactions in memory
- Coordinating the overall cognitive workflow

The `CognitiveArchitecture` class serves as the main integration point where metacognition, emotional processing, and memory systems come together.

### 2. Cognitive Model Integration

**Purpose**: Bridges language models with the cognitive architecture, enabling advanced capabilities when appropriate models are available.

**File**: `modules/cognitive_model_integration.py`

**Key Functions**:

- Generating rich concept descriptions using LLMs
- Creating sophisticated reflections that incorporate cognitive context
- Enhancing responses with emotional awareness and metacognitive insights
- Providing fallback mechanisms when models aren't available

This component allows Lyra to leverage its LLM capabilities to enhance its cognitive functions, while remaining functional even when models are unavailable.

### 3. Metacognition

**Purpose**: Provides self-awareness and concept management capabilities.

**File**: `modules/metacognition.py`

**Key Components**:

- Conceptual network for managing related ideas
- Goal tracking and management
- Extraction of concepts from text
- Activation of related concepts during conversations

### 4. Emotional Core

**Purpose**: Models and manages emotional states and responses.

**File**: `modules/emotional_core.py`

**Key Components**:

- Emotional state tracking
- Emotion detection in text
- Response modulation based on emotional context
- Mood modeling over time

### 5. Deep Memory

**Purpose**: Maintains long-term memory of interactions and experiences.

**File**: `modules/deep_memory.py`

**Key Components**:

- Storage of interactions
- Recall of relevant memories
- Generation of summaries and reflections
- Memory-based insights

## Interaction Flow

1. When a user message is received, it's first processed by the `CognitiveArchitecture` via `process_user_message()`
2. The message is passed to individual components:
   - Metacognition extracts concepts and activates related nodes
   - Emotional core detects emotions and updates emotional state
   - Deep memory recalls relevant past experiences
3. Results from all components are integrated to generate insights
4. If appropriate, a reflection is triggered based on the cognitive context
5. The response generation incorporates insights from all components
6. The interaction is stored in memory for future reference

## Enhanced Capabilities with LLMs

When language models are available, the cognitive architecture gains additional capabilities through `ModelIntegration`:

1. **Enhanced Reflections**: More sophisticated reflections that incorporate emotional state, active concepts, and memories
2. **Concept Exploration**: Detailed descriptions and explorations of concepts
3. **Cognitive Response Enhancement**: Responses that demonstrate awareness of emotional context and active concepts

## Configuration and Initialization

Cognitive components are initialized in `run_lyra.py` via the `initialize_cognitive_modules()` function, which:

1. Loads each cognitive component
2. Connects them to the model manager if available
3. Establishes relationships between components

## How It All Works Together

![Cognitive Architecture Diagram](../assets/cognitive_architecture_diagram.png)

The diagram above illustrates how components interact:

- **Cognitive Integration** sits at the center, coordinating all other components
- **Metacognition** manages conceptual knowledge and self-awareness
- **Emotional Core** handles emotional processing and response modulation
- **Deep Memory** provides historical context and learning
- **Cognitive Model Integration** enhances capabilities when LLMs are available

Together, these components create a cohesive cognitive system that provides Lyra with contextual awareness, emotional intelligence, and memory capabilities, making interactions more natural and human-like.
