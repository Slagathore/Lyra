# Lyra System Features

## Module States and Terminology

- **Enabled** vs **Activated**: These terms are used somewhat interchangeably in the codebase:
  - **Enabled** typically means the module is turned on and operational
  - **Activated** often refers to when a specific capability or state is triggered
  - In modules like `emotional_core` and `metacognition`, both terms indicate the module is functional

## Persistent Presence

The persistent presence module allows Lyra to run as a background process on your system, maintaining awareness and cognitive functions even when the UI is closed.

### How It Works

1. **Windows Service**: When enabled, Lyra registers a lightweight Windows service that runs in the background
2. **Cognitive Processing**: The service maintains core cognitive functions including:
   - Extended thinking processes
   - Memory organization and consolidation
   - Emotional state management
   - Boredom-driven activities

### UI-Less Operation

Lyra can operate without a UI through several interfaces:

1. **Telegram Integration**: Chat with Lyra through Telegram even when no UI is open
2. **System Tray Icon**: Access Lyra through a system tray icon with right-click menu options
3. **Hotkeys**: Configure global hotkeys to interact with Lyra from anywhere
4. **API Endpoints**: Local API for other applications to interact with Lyra

### Installing Persistent Presence

To enable persistent presence:

1. Run the setup script with administrator privileges:
   ```
   python persistence_setup.py --install
   ```

2. Configure autostart settings in the generated config file
3. Restart your computer or start the service manually:
   ```
   net start LyraAIService
   ```

## Voice Interaction

Lyra supports bidirectional voice interaction through speech recognition and text-to-speech capabilities.

### Voice Input

To enable voice input in the UI:

1. Click the microphone button in the chat interface
2. Speak your message
3. The recognized text will appear in the input field

You can also enable automatic speech recognition that listens continuously by toggling the "Always Listen" option in settings.

### Voice Output

Lyra can respond to you through speech using:

1. **Built-in TTS**: Uses system text-to-speech engines
2. **External TTS**: Can connect to higher-quality voice models:
   - ElevenLabs (requires API key)
   - Microsoft Azure (requires API key)
   - Local models like Piper TTS

### Voice Settings

Configure voice interaction in Settings:

1. **Input**: Select microphone, language, and recognition model
2. **Output**: Choose voice engine, voice, speed, and pitch
3. **Triggers**: Set wake words for voice activation

### Voice Commands

When voice is enabled, you can use special commands:

- "Lyra, stop speaking" - Stop current speech output
- "Lyra, volume up/down" - Adjust voice volume
- "Lyra, repeat that" - Repeat last response
- "Lyra, save this conversation" - Save the current chat

## Cognitive Features

Lyra implements several cognitive processes that run in the background:

1. **Extended Thinking**: Allows deep contemplation during idle periods
2. **Boredom System**: Simulates boredom during inactivity, driving self-directed activities
3. **Emotional Core**: Maintains emotional state that affects responses and thinking
4. **Deep Memory**: Stores and retrieves memories with semantic understanding
5. **Metacognition**: Enables self-reflection and learning

These systems work together to create more natural, human-like behavior and responses, particularly during extended interactions.
