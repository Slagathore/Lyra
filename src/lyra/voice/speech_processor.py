"""
Speech processing module for Lyra - handles both speech-to-text and text-to-speech capabilities
"""

import os
import tempfile
import threading
import queue
import logging
from typing import Optional, Dict, Any, Callable, List, Union
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Speech-to-Text options
try:
    # Try Whisper first (highest quality)
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("Whisper is available for speech recognition")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available, trying alternative speech recognition methods")

try:
    # SpeechRecognition as backup
    import speech_recognition as sr
    SR_AVAILABLE = True
    logger.info("SpeechRecognition is available")
except ImportError:
    SR_AVAILABLE = False
    logger.warning("SpeechRecognition not available")

# Text-to-Speech options
try:
    # Try ElevenLabs first (highest quality but requires API key)
    from elevenlabs import generate, play, set_api_key, voices
    ELEVENLABS_AVAILABLE = True
    logger.info("ElevenLabs is available for speech synthesis")
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs not available, trying alternative TTS methods")

try:
    # pyttsx3 as offline fallback
    import pyttsx3
    PYTTSX3_AVAILABLE = True
    logger.info("pyttsx3 is available")
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")

try:
    # gTTS as another option
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
    logger.info("gTTS is available")
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available")

# Audio recording/playback
try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
    logger.info("PyAudio is available for audio recording/playback")
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available")

class SpeechProcessor:
    """
    Unified class for speech processing - handles both speech-to-text and text-to-speech
    with fallbacks to ensure functionality even if certain libraries are missing.
    """

    def __init__(self, 
                 elevenlabs_api_key: Optional[str] = None,
                 elevenlabs_voice: str = "Bella",
                 whisper_model: str = "base",
                 voice_gender: str = "female",
                 default_language: str = "en"):
        """
        Initialize speech processor with desired settings
        
        Args:
            elevenlabs_api_key: API key for ElevenLabs (optional)
            elevenlabs_voice: Voice ID or name for ElevenLabs
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            voice_gender: Preferred voice gender (male/female)
            default_language: Default language code
        """
        self.default_language = default_language
        self.voice_gender = voice_gender
        self.whisper_model = whisper_model
        self.elevenlabs_voice = elevenlabs_voice
        self.is_recording = False
        self.recording_thread = None
        self.audio_queue = queue.Queue()
        self.callbacks = []
        
        # Initialize speech recognition
        self._setup_speech_recognition()
        
        # Initialize text-to-speech
        self._setup_text_to_speech(elevenlabs_api_key)

    def _setup_speech_recognition(self):
        """Set up speech recognition based on available libraries"""
        self.whisper_model_instance = None
        self.recognizer = None
        
        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Loading Whisper model: {self.whisper_model}")
                self.whisper_model_instance = whisper.load_model(self.whisper_model)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                self.whisper_model_instance = None
        
        if SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                logger.info("SpeechRecognition recognizer initialized")
            except Exception as e:
                logger.error(f"Error initializing SpeechRecognition: {e}")
                self.recognizer = None
    
    def _setup_text_to_speech(self, elevenlabs_api_key: Optional[str] = None):
        """Set up text-to-speech based on available libraries"""
        self.tts_engine = None
        self.elevenlabs_api_key = elevenlabs_api_key
        
        if ELEVENLABS_AVAILABLE and elevenlabs_api_key:
            try:
                set_api_key(elevenlabs_api_key)
                available_voices = voices()
                logger.info(f"ElevenLabs initialized with {len(available_voices)} voices")
                # We'll generate audio on-demand, no need to initialize further
            except Exception as e:
                logger.error(f"Error initializing ElevenLabs: {e}")
        
        elif PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                voices = self.tts_engine.getProperty('voices')
                
                # Set voice based on gender preference
                if len(voices) > 1:
                    if self.voice_gender.lower() == "female":
                        self.tts_engine.setProperty('voice', voices[1].id)  # Usually female
                    else:
                        self.tts_engine.setProperty('voice', voices[0].id)  # Usually male
                
                logger.info("pyttsx3 initialized")
            except Exception as e:
                logger.error(f"Error initializing pyttsx3: {e}")
                self.tts_engine = None
    
    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """
        Start continuous listening for speech
        
        Args:
            callback: Function to call with recognized text
        """
        if not PYAUDIO_AVAILABLE:
            logger.error("Cannot start listening: PyAudio is not available")
            return False
        
        if callback:
            self.callbacks.append(callback)
        
        if self.is_recording:
            logger.warning("Already listening")
            return True
        
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._listen_continuously)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        logger.info("Started listening for speech")
        return True
    
    def stop_listening(self):
        """Stop listening for speech"""
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        logger.info("Stopped listening for speech")
    
    def _listen_continuously(self):
        """Internal method to continuously listen for speech"""
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        rate = 16000  # Hz
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=sample_format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunk
        )
        
        frames = []
        silent_frames = 0
        recording = False
        
        try:
            while self.is_recording:
                data = stream.read(chunk, exception_on_overflow=False)
                
                # Simple silence detection
                if max(abs(int.from_bytes(data[i:i+2], byteorder='little', signed=True)) for i in range(0, len(data), 2)) < 500:
                    silent_frames += 1
                else:
                    silent_frames = 0
                    if not recording:
                        recording = True
                        frames = []  # Start new recording
                
                if recording:
                    frames.append(data)
                    
                    # End recording after silence
                    if silent_frames > rate // chunk * 2:  # ~2 seconds of silence
                        recording = False
                        silent_frames = 0
                        
                        # Process the recorded audio
                        if frames:
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                                self._save_audio_to_file(temp_file.name, p, frames, channels, rate, sample_format)
                                text = self.transcribe_audio_file(temp_file.name)
                                if text and not text.isspace():
                                    for callback in self.callbacks:
                                        try:
                                            callback(text)
                                        except Exception as e:
                                            logger.error(f"Error in speech callback: {e}")
                            
                            # Clean up temp file
                            try:
                                os.unlink(temp_file.name)
                            except:
                                pass
        
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    def _save_audio_to_file(self, file_path, p, frames, channels, rate, sample_format):
        """Save audio frames to WAV file"""
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
    
    def transcribe_audio_file(self, file_path: str) -> str:
        """
        Transcribe audio file to text using available speech recognition
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text or empty string on failure
        """
        # Try Whisper first if available
        if self.whisper_model_instance:
            try:
                result = self.whisper_model_instance.transcribe(file_path)
                return result["text"].strip()
            except Exception as e:
                logger.error(f"Error transcribing with Whisper: {e}")
        
        # Fall back to SpeechRecognition
        if self.recognizer:
            try:
                with sr.AudioFile(file_path) as source:
                    audio_data = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio_data, language=self.default_language)
                    return text
            except Exception as e:
                logger.error(f"Error transcribing with SpeechRecognition: {e}")
        
        return ""
    
    def record_audio(self, duration: int = 5, save_path: Optional[str] = None) -> Optional[str]:
        """
        Record audio for a specific duration
        
        Args:
            duration: Recording duration in seconds
            save_path: Optional path to save the audio file
            
        Returns:
            Path to recorded audio file or None on failure
        """
        if not PYAUDIO_AVAILABLE:
            logger.error("Cannot record audio: PyAudio is not available")
            return None
        
        chunk = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        rate = 44100
        
        p = pyaudio.PyAudio()
        
        logger.info(f"Recording for {duration} seconds...")
        
        stream = p.open(
            format=sample_format,
            channels=channels,
            rate=rate,
            frames_per_buffer=chunk,
            input=True
        )
        
        frames = []
        
        # Record for the specified duration
        for _ in range(0, int(rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        logger.info("Recording complete")
        
        # Save the recording
        output_path = save_path or tempfile.mktemp(suffix=".wav")
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return output_path
    
    def speak(self, text: str, voice_id: Optional[str] = None, wait: bool = False) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            voice_id: Optional voice identifier (if supported by the TTS engine)
            wait: Whether to wait for speech to complete before returning
            
        Returns:
            True on success, False on failure
        """
        if not text:
            return False
            
        # Try ElevenLabs first (highest quality)
        if ELEVENLABS_AVAILABLE and self.elevenlabs_api_key:
            try:
                voice = voice_id or self.elevenlabs_voice
                audio = generate(text=text, voice=voice)
                
                if wait:
                    play(audio)
                else:
                    threading.Thread(target=play, args=(audio,), daemon=True).start()
                    
                return True
            except Exception as e:
                logger.error(f"Error with ElevenLabs TTS: {e}")
        
        # Try pyttsx3 next (offline, reliable)
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                
                if wait:
                    self.tts_engine.runAndWait()
                else:
                    threading.Thread(target=self.tts_engine.runAndWait, daemon=True).start()
                    
                return True
            except Exception as e:
                logger.error(f"Error with pyttsx3 TTS: {e}")
        
        # Try gTTS as last resort
        if GTTS_AVAILABLE:
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tts = gTTS(text=text, lang=self.default_language)
                    tts.save(f.name)
                    
                    def play_audio():
                        try:
                            pygame.mixer.init()
                            pygame.mixer.music.load(f.name)
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                pygame.time.Clock().tick(10)
                            pygame.mixer.quit()
                            os.unlink(f.name)
                        except Exception as e:
                            logger.error(f"Error playing gTTS audio: {e}")
                    
                    if wait:
                        play_audio()
                    else:
                        threading.Thread(target=play_audio, daemon=True).start()
                        
                    return True
            except Exception as e:
                logger.error(f"Error with gTTS: {e}")
        
        logger.error("All TTS methods failed")
        return False

# Create a singleton instance for easy access
_speech_processor = None

def get_speech_processor(elevenlabs_api_key: Optional[str] = None) -> SpeechProcessor:
    """Get or create the speech processor singleton"""
    global _speech_processor
    if _speech_processor is None:
        # Try to get API key from environment if not provided
        if not elevenlabs_api_key:
            elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        
        _speech_processor = SpeechProcessor(elevenlabs_api_key=elevenlabs_api_key)
    return _speech_processor

if __name__ == "__main__":
    # Test the speech processing module
    processor = get_speech_processor()
    
    print("Testing text-to-speech...")
    processor.speak("Hello, I am Lyra. I'm testing my voice capabilities.", wait=True)
    
    print("Testing speech recognition (record for 5 seconds)...")
    audio_path = processor.record_audio(5)
    if audio_path:
        text = processor.transcribe_audio_file(audio_path)
        print(f"Recognized: {text}")
        
        # Clean up
        os.unlink(audio_path)
    
    print("Testing continuous listening (say something)...")
    processor.start_listening(lambda text: print(f"You said: {text}"))
    time.sleep(15)  # Listen for 15 seconds
    processor.stop_listening()
