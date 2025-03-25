"""
Voice handling module for Lyra that manages text-to-speech operations
"""
import os
import tempfile
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("voice_handler")

class VoiceHandler:
    """Handles text-to-speech operations for Lyra"""
    
    def __init__(self, config_path: str = 'config/voice_config.json'):
        """Initialize the voice handler"""
        self.config_path = config_path
        self.config = self._load_config()
        self.tts_engine = None
        self.voices = []
        self.initialized = False
        
        # Try to initialize TTS engine
        self._init_tts_engine()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load voice configuration from JSON file"""
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "engine": "system",  # system, pyttsx3, gtts, etc.
                    "voice_id": "",
                    "rate": 150,
                    "volume": 1.0,
                    "pitch": 1.0,
                    "enabled": False,
                    "output_device": "default"
                }
                
                # Create directory if it doesn't exist
                config_path.parent.mkdir(exist_ok=True, parents=True)
                
                # Save default config
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
        except Exception as e:
            logger.error(f"Error loading voice config: {str(e)}")
            return {
                "engine": "system",
                "enabled": False
            }
    
    def _save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving voice config: {str(e)}")
    
    def _init_tts_engine(self) -> None:
        """Initialize the text-to-speech engine based on configuration"""
        engine_type = self.config.get("engine", "system")
        
        try:
            if engine_type == "pyttsx3":
                self._init_pyttsx3()
            elif engine_type == "gtts":
                self._init_gtts()
            elif engine_type == "system":
                self._init_system_tts()
            else:
                logger.warning(f"Unknown TTS engine type: {engine_type}")
                return
            
            self.initialized = True
            logger.info(f"Initialized {engine_type} TTS engine")
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {str(e)}")
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3 TTS engine"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Set properties from config
            self.tts_engine.setProperty('rate', self.config.get('rate', 150))
            self.tts_engine.setProperty('volume', self.config.get('volume', 1.0))
            
            # Set voice if specified
            voice_id = self.config.get('voice_id', '')
            if voice_id:
                self.tts_engine.setProperty('voice', voice_id)
            
            # Get available voices
            self.voices = self.tts_engine.getProperty('voices')
        except ImportError:
            logger.warning("pyttsx3 not installed, cannot initialize TTS engine")
            raise
    
    def _init_gtts(self) -> None:
        """Initialize Google Text-to-Speech"""
        try:
            from gtts import gTTS
            # gTTS doesn't need initialization, just make sure it's importable
            self.tts_engine = "gtts"
        except ImportError:
            logger.warning("gTTS not installed, cannot initialize TTS engine")
            raise
    
    def _init_system_tts(self) -> None:
        """Initialize system TTS (platform dependent)"""
        if os.name == 'nt':  # Windows
            try:
                import win32com.client
                self.tts_engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.initialized = True
            except ImportError:
                logger.warning("win32com not installed, cannot initialize Windows TTS")
                self.initialized = False
        else:  # Unix-like systems
            # Check for 'say' on macOS or 'espeak' on Linux
            if os.system("which say > /dev/null 2>&1") == 0:
                self.tts_engine = "say"
                self.initialized = True
            elif os.system("which espeak > /dev/null 2>&1") == 0:
                self.tts_engine = "espeak"
                self.initialized = True
            else:
                logger.warning("No system TTS found")
                self.initialized = False
    
    def speak(self, text: str, voice_id: Optional[str] = None) -> bool:
        """Convert text to speech using the configured engine"""
        if not self.config.get("enabled", False):
            logger.info("TTS is disabled, not speaking")
            return False
        
        if not self.initialized:
            logger.warning("TTS engine not initialized, cannot speak")
            return False
        
        try:
            engine_type = self.config.get("engine", "system")
            
            if voice_id is None:
                voice_id = self.config.get("voice_id", "")
            
            if engine_type == "pyttsx3":
                return self._speak_pyttsx3(text, voice_id)
            elif engine_type == "gtts":
                return self._speak_gtts(text, voice_id)
            elif engine_type == "system":
                return self._speak_system(text, voice_id)
            else:
                logger.warning(f"Unknown TTS engine type: {engine_type}")
                return False
        except Exception as e:
            logger.error(f"Error speaking text: {str(e)}")
            return False
    
    def _speak_pyttsx3(self, text: str, voice_id: str) -> bool:
        """Speak using pyttsx3"""
        try:
            if voice_id and self.voices:
                self.tts_engine.setProperty('voice', voice_id)
            
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Error with pyttsx3: {str(e)}")
            return False
    
    def _speak_gtts(self, text: str, voice_id: str) -> bool:
        """Speak using Google Text-to-Speech"""
        try:
            from gtts import gTTS
            import pygame
            
            # voice_id in gTTS is actually language code like 'en', 'fr', etc.
            lang = voice_id if voice_id else 'en'
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # Generate and save the speech
            tts = gTTS(text=text, lang=lang)
            tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.init()
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            # Clean up
            pygame.mixer.quit()
            os.remove(temp_filename)
            
            return True
        except Exception as e:
            logger.error(f"Error with gTTS: {str(e)}")
            return False
    
    def _speak_system(self, text: str, voice_id: str) -> bool:
        """Speak using system TTS"""
        try:
            if os.name == 'nt':  # Windows
                if voice_id:
                    # Set voice if specified
                    for voice in self.tts_engine.GetVoices():
                        if voice.Id == voice_id:
                            self.tts_engine.Voice = voice
                            break
                
                self.tts_engine.Speak(text)
                return True
            elif self.tts_engine == "say":  # macOS
                voice_param = f"-v {voice_id}" if voice_id else ""
                os.system(f'say {voice_param} "{text}"')
                return True
            elif self.tts_engine == "espeak":  # Linux
                voice_param = f"-v {voice_id}" if voice_id else ""
                os.system(f'espeak {voice_param} "{text}"')
                return True
            else:
                logger.warning("No supported system TTS available")
                return False
        except Exception as e:
            logger.error(f"Error with system TTS: {str(e)}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices"""
        voice_list = []
        
        try:
            engine_type = self.config.get("engine", "system")
            
            if engine_type == "pyttsx3" and self.tts_engine:
                for voice in self.voices:
                    voice_list.append({
                        "id": voice.id,
                        "name": voice.name,
                        "languages": voice.languages
                    })
            elif engine_type == "system" and os.name == 'nt' and self.tts_engine:
                for voice in self.tts_engine.GetVoices():
                    voice_list.append({
                        "id": voice.Id,
                        "name": voice.GetDescription()
                    })
            # For other engines, we'd need to implement specific methods
            
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
        
        return voice_list
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update voice settings"""
        try:
            self.config.update(settings)
            self._save_config()
            
            # Reinitialize if engine changed
            if "engine" in settings:
                self._init_tts_engine()
            elif self.initialized:
                # Update engine settings
                if "rate" in settings and hasattr(self.tts_engine, "setProperty"):
                    self.tts_engine.setProperty('rate', settings["rate"])
                
                if "volume" in settings and hasattr(self.tts_engine, "setProperty"):
                    self.tts_engine.setProperty('volume', settings["volume"])
                
                if "voice_id" in settings and hasattr(self.tts_engine, "setProperty"):
                    self.tts_engine.setProperty('voice', settings["voice_id"])
            
            return True
        except Exception as e:
            logger.error(f"Error updating voice settings: {str(e)}")
            return False
