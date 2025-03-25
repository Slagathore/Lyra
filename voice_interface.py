"""
Voice Interface for Lyra
Enables speech recognition and text-to-speech capabilities
"""

import os
import time
import json
import queue
import logging
import threading
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("voice.log")
    ]
)
logger = logging.getLogger("voice_interface")

class SpeechRecognizer:
    """Handles speech recognition for voice input"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config", "voice_config.json"
        )
        
        self.config = self._load_config()
        self.initialized = False
        self.listening = False
        self.recognition_thread = None
        self.stop_listening = threading.Event()
        self.speech_queue = queue.Queue()
        
        # Try to load speech recognition modules
        try:
            import speech_recognition as sr
            self.sr = sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = self.config.get("energy_threshold", 300)
            self.recognizer.dynamic_energy_threshold = self.config.get("dynamic_energy", True)
            self.recognizer.pause_threshold = self.config.get("pause_threshold", 0.8)
            self.recognizer.phrase_threshold = self.config.get("phrase_threshold", 0.3)
            self.recognizer.non_speaking_duration = self.config.get("non_speaking_duration", 0.5)
            
            self.initialized = True
            logger.info("Speech recognition initialized successfully")
        except ImportError:
            logger.warning("Speech recognition not available. Install with: pip install SpeechRecognition")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load voice configuration from file"""
        default_config = {
            "recognition_engine": "google",  # google, sphinx, azure, whisper
            "language": "en-US",
            "energy_threshold": 300,
            "dynamic_energy": True,
            "pause_threshold": 0.8,
            "phrase_threshold": 0.3,
            "non_speaking_duration": 0.5,
            "always_listen": False,
            "wake_word": "lyra",
            "api_keys": {}
        }
        
        if not os.path.exists(self.config_path):
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save default config
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        # Load existing config
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update with any missing default values
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"Error loading voice config: {e}")
            return default_config
    
    def start_listening(self):
        """Start listening for speech input"""
        if not self.initialized:
            logger.error("Speech recognition not initialized")
            return False
        
        if self.listening:
            logger.warning("Already listening")
            return True
        
        self.stop_listening.clear()
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()
        self.listening = True
        logger.info("Started speech recognition")
        return True
    
    def stop_listening(self):
        """Stop listening for speech input"""
        if not self.listening:
            return
        
        self.stop_listening.set()
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
        
        self.listening = False
        logger.info("Stopped speech recognition")
    
    def _recognition_loop(self):
        """Background thread for continuous speech recognition"""
        logger.info("Recognition loop started")
        
        # Try to use microphone
        try:
            with self.sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Ready for voice input")
                
                while not self.stop_listening.is_set():
                    try:
                        # Listen for audio
                        audio = self.recognizer.listen(
                            source, 
                            timeout=10.0, 
                            phrase_time_limit=self.config.get("phrase_time_limit", 15)
                        )
                        
                        # Process audio in separate thread to avoid blocking
                        threading.Thread(
                            target=self._process_audio,
                            args=(audio,),
                            daemon=True
                        ).start()
                    except self.sr.WaitTimeoutError:
                        # Timeout, continue listening
                        continue
                    except Exception as e:
                        logger.error(f"Error in recognition loop: {e}")
                        time.sleep(1)  # Avoid tight loop on error
        except Exception as e:
            logger.error(f"Error accessing microphone: {e}")
            self.listening = False
    
    def _process_audio(self, audio):
        """Process audio data and attempt recognition"""
        try:
            engine = self.config.get("recognition_engine", "google").lower()
            language = self.config.get("language", "en-US")
            
            # Recognize using the selected engine
            if engine == "google":
                text = self.recognizer.recognize_google(audio, language=language)
            elif engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio, language=language)
            elif engine == "azure":
                api_key = self.config.get("api_keys", {}).get("azure")
                if not api_key:
                    logger.error("Azure API key not found in config")
                    return
                text = self.recognizer.recognize_azure(audio, key=api_key, language=language)
            elif engine == "whisper":
                # Try to use local whisper if available
                try:
                    from whisper_recognition import recognize_whisper
                    text = recognize_whisper(audio)
                except ImportError:
                    text = self.recognizer.recognize_whisper(audio, language=language)
            else:
                logger.error(f"Unknown recognition engine: {engine}")
                return
            
            # Add recognized speech to the queue
            if text:
                logger.info(f"Recognized: {text}")
                self.speech_queue.put(text)
        except self.sr.UnknownValueError:
            logger.debug("Speech not understood")
        except self.sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
    
    def get_speech(self, timeout: float = 0.1) -> Optional[str]:
        """
        Get recognized speech from the queue
        
        Args:
            timeout: How long to wait for speech (seconds)
            
        Returns:
            Recognized text or None if queue is empty
        """
        try:
            return self.speech_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def listen_once(self) -> Optional[str]:
        """
        Listen for a single utterance and return the recognized text
        
        Returns:
            Recognized text or None if recognition failed
        """
        if not self.initialized:
            logger.error("Speech recognition not initialized")
            return None
        
        try:
            with self.sr.Microphone() as source:
                logger.info("Listening for single utterance...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10.0, phrase_time_limit=15)
                
                # Process the audio
                engine = self.config.get("recognition_engine", "google").lower()
                language = self.config.get("language", "en-US")
                
                # Recognize using the selected engine
                if engine == "google":
                    text = self.recognizer.recognize_google(audio, language=language)
                elif engine == "sphinx":
                    text = self.recognizer.recognize_sphinx(audio, language=language)
                elif engine == "azure":
                    api_key = self.config.get("api_keys", {}).get("azure")
                    if not api_key:
                        logger.error("Azure API key not found in config")
                        return None
                    text = self.recognizer.recognize_azure(audio, key=api_key, language=language)
                elif engine == "whisper":
                    # Try to use local whisper if available
                    try:
                        from whisper_recognition import recognize_whisper
                        text = recognize_whisper(audio)
                    except ImportError:
                        text = self.recognizer.recognize_whisper(audio, language=language)
                else:
                    logger.error(f"Unknown recognition engine: {engine}")
                    return None
                
                logger.info(f"Recognized: {text}")
                return text
        except self.sr.UnknownValueError:
            logger.debug("Speech not understood")
            return None
        except self.sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return None

class TextToSpeech:
    """Handles text-to-speech for voice output"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config", "voice_config.json"
        )
        
        self.config = self._load_config()
        self.initialized = False
        self.speaking = False
        self.speak_thread = None
        self.stop_speaking = threading.Event()
        
        # Try to load text-to-speech modules
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure the engine
            voice_id = self.config.get("voice_id")
            if voice_id:
                self.engine.setProperty('voice', voice_id)
            
            # Set rate and volume
            self.engine.setProperty('rate', self.config.get("speech_rate", 175))
            self.engine.setProperty('volume', self.config.get("volume", 1.0))
            
            self.initialized = True
            logger.info("Text-to-speech initialized successfully")
        except ImportError:
            logger.warning("pyttsx3 not available. Install with: pip install pyttsx3")
            self._try_alternative_tts()
    
    def _try_alternative_tts(self):
        """Try to initialize alternative TTS methods"""
        # Try using platform-specific TTS
        import platform
        system = platform.system()
        
        if system == "Windows":
            try:
                import win32com.client
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.initialized = True
                logger.info("Initialized Windows SAPI TTS")
            except ImportError:
                logger.warning("win32com not available on Windows")
        elif system == "Darwin":  # macOS
            self.engine = "say"  # Use macOS 'say' command
            self.initialized = True
            logger.info("Initialized macOS TTS")
        elif system == "Linux":
            # Try espeak
            try:
                subprocess.run(["espeak", "--version"], check=True, capture_output=True)
                self.engine = "espeak"
                self.initialized = True
                logger.info("Initialized espeak TTS")
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("espeak not available on Linux")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load voice configuration from file"""
        default_config = {
            "tts_engine": "system",  # system, elevenlabs, azure, piper
            "voice_id": None,
            "speech_rate": 175,
            "volume": 1.0,
            "pitch": 1.0,
            "api_keys": {}
        }
        
        if not os.path.exists(self.config_path):
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save default config
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        # Load existing config
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Update with any missing default values
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"Error loading voice config: {e}")
            return default_config
    
    def speak(self, text: str):
        """
        Speak the given text
        
        Args:
            text: Text to speak
        """
        if not self.initialized:
            logger.error("Text-to-speech not initialized")
            return
        
        # Stop any current speech
        self.stop_speaking.set()
        if self.speak_thread and self.speak_thread.is_alive():
            self.speak_thread.join(timeout=1.0)
        
        self.stop_speaking.clear()
        self.speak_thread = threading.Thread(target=self._speak_thread, args=(text,), daemon=True)
        self.speak_thread.start()
    
    def _speak_thread(self, text: str):
        """Background thread for speech synthesis"""
        self.speaking = True
        
        try:
            tts_engine = self.config.get("tts_engine", "system").lower()
            
            if tts_engine == "system":
                self._system_tts(text)
            elif tts_engine == "elevenlabs":
                self._elevenlabs_tts(text)
            elif tts_engine == "azure":
                self._azure_tts(text)
            elif tts_engine == "piper":
                self._piper_tts(text)
            else:
                logger.error(f"Unknown TTS engine: {tts_engine}")
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
        finally:
            self.speaking = False
    
    def _system_tts(self, text: str):
        """Use system TTS engine"""
        import platform
        system = platform.system()
        
        if isinstance(self.engine, str):
            # Command-line TTS
            if self.engine == "say":  # macOS
                subprocess.run(["say", text], check=False)
            elif self.engine == "espeak":  # Linux
                subprocess.run(["espeak", text], check=False)
        elif system == "Windows" and "win32com" in str(type(self.engine)):
            # Windows SAPI
            self.engine.Speak(text)
        else:
            # pyttsx3
            self.engine.say(text)
            self.engine.runAndWait()
    
    def _elevenlabs_tts(self, text: str):
        """Use ElevenLabs for TTS"""
        try:
            import requests
            
            api_key = self.config.get("api_keys", {}).get("elevenlabs")
            if not api_key:
                logger.error("ElevenLabs API key not found in config")
                return
            
            voice_id = self.config.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Play the audio
                import tempfile
                import platform
                import subprocess
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                system = platform.system()
                
                try:
                    if system == "Windows":
                        os.startfile(temp_path)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["afplay", temp_path], check=False)
                    else:  # Linux
                        subprocess.run(["mpg123", temp_path], check=False)
                finally:
                    # Wait a bit before deleting the file to allow playback to start
                    time.sleep(0.5)
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} {response.text}")
        except ImportError:
            logger.error("requests module not available for ElevenLabs TTS")
        except Exception as e:
            logger.error(f"Error in ElevenLabs TTS: {e}")
    
    def _azure_tts(self, text: str):
        """Use Azure for TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            api_key = self.config.get("api_keys", {}).get("azure_speech")
            region = self.config.get("azure_region", "eastus")
            
            if not api_key:
                logger.error("Azure Speech API key not found in config")
                return
            
            # Set up Azure speech configuration
            speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
            
            # Configure voice
            voice_name = self.config.get("azure_voice", "en-US-JennyNeural")
            speech_config.speech_synthesis_voice_name = voice_name
            
            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            
            # Synthesize text
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.error(f"Azure TTS error: {result.reason}")
        except ImportError:
            logger.error("Azure Speech SDK not available")
        except Exception as e:
            logger.error(f"Error in Azure TTS: {e}")
    
    def _piper_tts(self, text: str):
        """Use local Piper TTS"""
        try:
            piper_path = self.config.get("piper_path")
            model_path = self.config.get("piper_model")
            
            if not piper_path or not model_path:
                logger.error("Piper path or model not specified in config")
                return
            
            # Create piper command
            cmd = [piper_path, "--model", model_path, "--output_raw"]
            
            # Run piper command
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send text to piper
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode != 0:
                logger.error(f"Piper TTS error: {stderr}")
            
            # Play the audio (requires aplay on Linux, etc.)
            # This is a simplified example
            import platform
            system = platform.system()
            
            if system == "Linux":
                subprocess.run(["aplay"], input=stdout.encode(), check=False)
            else:
                logger.error(f"Piper TTS output playback not implemented for {system}")
        except Exception as e:
            logger.error(f"Error in Piper TTS: {e}")
    
    def stop(self):
        """Stop current speech"""
        self.stop_speaking.set()
        
        # Try to stop the engine
        try:
            import platform
            system = platform.system()
            
            if system == "Windows" and hasattr(self.engine, "pause"):
                self.engine.pause()
            elif system == "Darwin":  # macOS
                subprocess.run(["killall", "say"], check=False)
            elif system == "Linux":
                subprocess.run(["killall", "espeak"], check=False)
                subprocess.run(["killall", "mpg123"], check=False)
        except Exception as e:
            logger.debug(f"Error stopping speech: {e}")
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.speaking
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        voices = []
        
        if not self.initialized:
            return voices
        
        try:
            import platform
            system = platform.system()
            
            if system == "Windows" and "win32com" in str(type(self.engine)):
                # Windows SAPI
                for voice in self.engine.GetVoices():
                    voices.append({
                        "id": voice.Id,
                        "name": voice.GetDescription(),
                        "language": voice.GetAttribute("Language")
                    })
            elif not isinstance(self.engine, str):
                # pyttsx3
                for voice in self.engine.getProperty('voices'):
                    voices.append({
                        "id": voice.id,
                        "name": voice.name,
                        "language": voice.languages[0] if voice.languages else "unknown"
                    })
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
        
        return voices

class VoiceInterface:
    """Main voice interface integrating speech recognition and synthesis"""
    
    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.text_to_speech = TextToSpeech()
        self.enabled = False
        self.always_listen = False
        self.wake_word = "lyra"
        self.voice_command_handlers = {}
        
        # Register basic voice commands
        self._register_default_commands()
        
        # Start if configuration specifies
        config = self._load_config()
        if config.get("auto_start", False):
            self.start()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load voice configuration from file"""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config", "voice_config.json"
        )
        
        default_config = {
            "auto_start": False,
            "always_listen": False,
            "wake_word": "lyra",
            "voice_commands_enabled": True
        }
        
        if not os.path.exists(config_path):
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        # Load existing config
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update with any missing default values
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            # Update instance variables
            self.always_listen = config.get("always_listen", False)
            self.wake_word = config.get("wake_word", "lyra").lower()
            
            return config
        except Exception as e:
            logger.error(f"Error loading voice config: {e}")
            return default_config
    
    def _register_default_commands(self):
        """Register default voice commands"""
        self.register_command("stop speaking", self.stop_speaking)
        self.register_command("be quiet", self.stop_speaking)
        self.register_command("volume up", self._volume_up)
        self.register_command("volume down", self._volume_down)
        self.register_command("repeat that", self._repeat_last)
        self.register_command("help", self._help_command)
    
    def start(self) -> bool:
        """Start the voice interface"""
        if not self.speech_recognizer.initialized or not self.text_to_speech.initialized:
            logger.error("Voice modules not properly initialized")
            return False
        
        # Start the speech recognizer
        if not self.speech_recognizer.start_listening():
            return False
        
        self.enabled = True
        logger.info("Voice interface started")
        return True
    
    def stop(self):
        """Stop the voice interface"""
        if not self.enabled:
            return
        
        # Stop the speech recognizer
        self.speech_recognizer.stop_listening()
        
        # Stop any ongoing speech
        self.text_to_speech.stop()
        
        self.enabled = False
        logger.info("Voice interface stopped")
    
    def speak(self, text: str):
        """
        Speak the given text
        
        Args:
            text: Text to speak
        """
        if not self.enabled:
            logger.warning("Voice interface not enabled")
            return
        
        self.text_to_speech.speak(text)
        
        # Store the last spoken text for repeat command
        self.last_spoken_text = text
    
    def stop_speaking(self):
        """Stop current speech"""
        self.text_to_speech.stop()
    
    def listen_once(self) -> Optional[str]:
        """
        Listen for a single utterance
        
        Returns:
            Recognized text or None if recognition failed
        """
        if not self.enabled:
            logger.warning("Voice interface not enabled")
            return None
        
        return self.speech_recognizer.listen_once()
    
    def process_speech(self) -> Tuple[bool, Optional[str]]:
        """
        Process speech from the recognition queue
        
        Returns:
            Tuple of (is_command, recognized_text)
            - is_command: True if the speech was handled as a command
            - recognized_text: The recognized text, or None if no speech was recognized
        """
        if not self.enabled:
            return False, None
        
        # Get recognized speech
        text = self.speech_recognizer.get_speech()
        
        if not text:
            return False, None
        
        # Check if this is a wake word activation
        if not self.always_listen and self.wake_word:
            if not text.lower().startswith(self.wake_word.lower()):
                # Not activated, ignore
                return False, None
            
            # Remove wake word from the text
            text = text[len(self.wake_word):].strip()
            
            # If nothing left after wake word, just acknowledge
            if not text:
                self.speak("Yes?")
                return True, None
        
        # Check for voice commands
        for command, handler in self.voice_command_handlers.items():
            if command in text.lower():
                # Execute the command
                handler()
                return True, None
        
        # Return the recognized text for normal processing
        return False, text
    
    def register_command(self, command: str, handler):
        """
        Register a voice command handler
        
        Args:
            command: The command phrase to listen for
            handler: Function to call when command is recognized
        """
        self.voice_command_handlers[command.lower()] = handler
    
    def _volume_up(self):
        """Increase voice volume"""
        if hasattr(self.text_to_speech.engine, "getProperty") and hasattr(self.text_to_speech.engine, "setProperty"):
            current_volume = self.text_to_speech.engine.getProperty('volume')
            new_volume = min(1.0, current_volume + 0.1)
            self.text_to_speech.engine.setProperty('volume', new_volume)
            self.speak(f"Volume increased to {int(new_volume * 100)}%")
    
    def _volume_down(self):
        """Decrease voice volume"""
        if hasattr(self.text_to_speech.engine, "getProperty") and hasattr(self.text_to_speech.engine, "setProperty"):
            current_volume = self.text_to_speech.engine.getProperty('volume')
            new_volume = max(0.1, current_volume - 0.1)
            self.text_to_speech.engine.setProperty('volume', new_volume)
            self.speak(f"Volume decreased to {int(new_volume * 100)}%")
    
    def _repeat_last(self):
        """Repeat the last spoken text"""
        if hasattr(self, "last_spoken_text") and self.last_spoken_text:
            self.speak(self.last_spoken_text)
        else:
            self.speak("I don't have anything to repeat")
    
    def _help_command(self):
        """Provide help information about voice commands"""
        help_text = "Available voice commands: "
        commands = list(self.voice_command_handlers.keys())
        help_text += ", ".join(commands)
        self.speak(help_text)

# Singleton instance
_voice_interface_instance = None

def get_instance():
    """Get the singleton instance of VoiceInterface"""
    global _voice_interface_instance
    if _voice_interface_instance is None:
        _voice_interface_instance = VoiceInterface()
    return _voice_interface_instance

# Main function for standalone testing
def main():
    """Run the voice interface as a standalone application"""
    parser = argparse.ArgumentParser(description="Lyra Voice Interface")
    parser.add_argument("--speak", type=str, help="Text to speak")
    parser.add_argument("--listen", action="store_true", help="Listen for speech")
    args = parser.parse_args()
    
    voice_interface = get_instance()
    
    if args.speak:
        voice_interface.start()
        voice_interface.speak(args.speak)
        time.sleep(5)  # Wait for speech to complete
        voice_interface.stop()
    elif args.listen:
        voice_interface.start()
        print("Listening... Press Ctrl+C to stop")
        try:
            while True:
                is_command, text = voice_interface.process_speech()
                if text:
                    print(f"Recognized: {text}")
                    voice_interface.speak(f"You said: {text}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            voice_interface.stop()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
