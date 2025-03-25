# Collaborative Improvement Module

The Collaborative Improvement Module is a system that enables Lyra to learn and improve through conversations with humans. It combines several advanced techniques including deep learning analysis, consultation with other LLMs, and reinforcement learning to continuously enhance its capabilities.

## Features

- **Interactive learning through conversation**: Engage in natural conversations that help the AI learn and grow
- **Multi-stage improvement process**: Combines text processing, deep learning, LLM consultation, and human feedback
- **Advanced media generation integration**:
  - Images via Stable Diffusion
  - Videos via ComfyUI and Wan2
  - 3D models via various generators
- **Code self-improvement**: The system can suggest and implement improvements to its own codebase
- **Session management**: Conversations and learning progress are saved for future reference
- **Data visualization**: Creates visualizations of insights when appropriate topics are discussed
- **API access**: External tools can interact with the system via a RESTful API

## How It Works

1. **Conversation**: The module starts a conversation with you on a topic of interest
2. **Text Processing**: Your responses are cleaned and analyzed to extract key concepts
3. **Deep Learning**: The system creates embeddings and identifies themes in the conversation
4. **LLM Consultation**: Other specialized AI systems provide feedback and insights
5. **Reinforcement Learning**: The system learns from all of these inputs to improve its responses
6. **Code Improvement**: Based on what it learns, the system can suggest improvements to its own code

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages: gradio, numpy, etc. (see `is_available()` function for full list)

### Running the Module

```bash
python collaborative_improvement_app.py
```

### Command Line Options

- `--config PATH`: Path to a custom configuration file
- `--port PORT`: Port to run the Gradio interface on (default: 7860)
- `--no-media`: Disable media generation capabilities
- `--auto-improve`: Enable automatic code improvements
- `--check-improvements`: Check for pending code improvements without applying them

## Examples

### Starting a Conversation

When you launch the module, it will start by suggesting a topic for discussion. You can either continue with that topic or introduce your own.

### Requesting Media

You can ask the system to generate media with simple phrases:

- "Create an image of a sunset over mountains"
- "Generate a video showing a flower blooming using ComfyUI"
- "Make a 3D model of a futuristic car"
- "Create a 10 seconds video of ocean waves with Wan2"

You can specify parameters like:

- For videos: fps, duration, style (cinematic, anime, realistic, etc.)
- For images: resolution, style
- For 3D: complexity level

### Viewing Improvement Suggestions

The system will occasionally suggest improvements to its own code. These are saved in the `improvements/suggestions` directory and can be viewed or applied manually.

## Architecture

The module consists of several key components:

- **TextProcessor**: Cleans and analyzes text input
- **DeepLearner**: Creates embeddings and identifies themes
- **LLMConsultant**: Consults with other AI systems for insights
- **ReinforcementLearner**: Updates the system based on feedback
- **CodeImprover**: Suggests improvements to the codebase
- **MediaIntegrator**: Handles media generation requests
  - Supports multiple video generators (ComfyUI, Wan2)
  - Integrates with image generators
  - Provides 3D model generation
- **CodeUpdater**: Implements suggested code improvements

## Advanced Features

### REST API

The module provides a RESTful API for external tools to interact with it:

```bash
# Start the API server
python -m modules.improvement_api
```

API endpoints:

- `POST /message` - Process a message and get a response
- `POST /generate-media` - Generate media (image/video/3D)
- `POST /suggest-improvement` - Suggest a code improvement

### Self-Modification

The system can automatically implement code improvements:

```bash
# Check for pending improvements
python collaborative_improvement_app.py --check-improvements

# Auto-implement high-impact improvements
python collaborative_improvement_app.py --auto-improve
```

### Data Visualization

The system can create visualizations to represent insights from conversations.
These are automatically generated when discussing topics related to data or statistics.

## Extending the System

The collaborative improvement module is designed to be extensible:

1. **New Media Types**: Add new generators to the `MediaIntegrator` class
   - For video generation, you can add new providers beyond ComfyUI and Wan2
   - Custom workflows can be defined in the ComfyUI integration
   - Different models can be specified for Wan2
2. **Additional LLMs**: Register new LLMs in the `LLMConsultant` class
3. **Custom Learning**: Modify the `ReinforcementLearner` to use different learning strategies

## Troubleshooting

- If you encounter errors about missing dependencies, check the logs for details
- Session files are stored in the `sessions` directory if you need to recover a conversation
- Backup files are created in `modules/backups` before any code changes are made

## Contributing

This module is part of the Lyra project. To contribute:

1. Create improvements to any of the components
2. Test your changes thoroughly
3. Document what you've changed
4. Submit your improvements

## License

This project is part of Lyra and follows the same licensing terms.

## Collaborative Improvement System

Lyra's collaborative improvement system allows multiple AI models to work together to refine and enhance content.

### Key Features

- Multi-model collaboration for iterative improvement
- Feedback-driven refinement process
- Support for text and code improvement
- Extensible architecture for adding new models

### Collaboration Process

The system works through these steps:

1. Content is submitted for improvement
2. Multiple models analyze and suggest improvements
3. Improvements are merged and prioritized
4. Final enhanced content is produced

### Benefits

This approach leads to better results than single-model approaches.
