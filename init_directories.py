"""
Ensure all required directories exist on startup
"""
import os
from pathlib import Path

# Define paths for all resources
MEMORY_DIR = Path('G:/AI/Lyra/memories')
NOTES_DIR = Path('G:/AI/Lyra/notes')
BOT_NOTES_DIR = Path('G:/AI/Lyra/bot_notes')
IMAGES_DIR = Path('G:/AI/Lyra/images')
VOICE_DIR = Path('G:/AI/Lyra/voice')
VIDEO_DIR = Path('G:/AI/Lyra/video')
CODE_DIR = Path('G:/AI/Lyra/code')
CONFIG_DIR = Path('G:/AI/Lyra/config')
CONTEXT_DIR = Path('G:/AI/Lyra/context')
ATTACHMENTS_DIR = Path('G:/AI/Lyra/attachments')
PRESETS_DIR = Path('G:/AI/Lyra/config/personality_presets')
ASSETS_DIR = Path('G:/AI/Lyra/assets')

# Create directories if they don't exist
DIRECTORIES = [
    MEMORY_DIR, NOTES_DIR, BOT_NOTES_DIR, 
    IMAGES_DIR, VOICE_DIR, VIDEO_DIR, 
    CODE_DIR, CONFIG_DIR, CONTEXT_DIR, 
    ATTACHMENTS_DIR, PRESETS_DIR, ASSETS_DIR
]

def init_directories():
    """Create all required directories if they don't exist"""
    for directory in DIRECTORIES:
        directory.mkdir(exist_ok=True, parents=True)
        print(f"Ensured directory exists: {directory}")

if __name__ == "__main__":
    init_directories()
