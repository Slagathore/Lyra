"""
Media Generation Interface for Lyra
Provides a unified API for generating images, audio, and video
"""

import os
import time
import logging
import json
import base64
import io
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import random
import threading
import queue

# Set up logging
logger = logging.getLogger("media_generation")

class MediaType(Enum):
    """Types of media that can be generated"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"

class MediaGenerator:
    """
    Unified interface for generating various types of media
    Acts as a façade to different generation backends
    """
    
    def __init__(self):
        """Initialize the media generator"""
        self.config = self._load_config()
        self.media_dir = Path(self.config.get("media_directory", "media"))
        self.media_dir.mkdir(exist_ok=True, parents=True)
        
        # Track available backends
        self.available_backends = {
            MediaType.IMAGE: [],
            MediaType.AUDIO: [],
            MediaType.VIDEO: [],
            MediaType.TEXT_TO_SPEECH: [],
            MediaType.SPEECH_TO_TEXT: []
        }
        
        # Initialize backends
        self._initialize_backends()
        
        # Task queue for async generation
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        # Track active tasks
        self.active_tasks = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = Path("config/media_config.json")
        default_config = {
            "media_directory": "media",
            "enable_image_generation": True,
            "enable_audio_generation": True, 
            "enable_video_generation": False,  # Disabled by default as it's more resource-intensive
            "enable_text_to_speech": True,
            "enable_speech_to_text": True,
            "preferred_backends": {
                "image": "stable_diffusion",
                "audio": "bark",
                "video": "stable_video_diffusion",
                "text_to_speech": "pyttsx3",
                "speech_to_text": "whisper"
            },
            "stability_api_key": "",
            "openai_api_key": "",
            "temperature": 0.7,
            "max_generation_time": 120  # seconds
        }
        
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    merged_config = {**default_config, **user_config}
                    
                    # Ensure nested dictionaries are merged
                    if "preferred_backends" in user_config:
                        merged_config["preferred_backends"] = {
                            **default_config["preferred_backends"],
                            **user_config["preferred_backends"]
                        }
                    
                    return merged_config
            except Exception as e:
                logger.error(f"Error loading media config: {e}")
        else:
            # Save default config if not exists
            try:
                config_file.parent.mkdir(exist_ok=True, parents=True)
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default media config at {config_file}")
            except Exception as e:
                logger.error(f"Error saving default media config: {e}")
        
        return default_config
    
    def _initialize_backends(self):
        """Initialize all available media generation backends"""
        # Initialize image backends
        if self.config.get("enable_image_generation", True):
            self._initialize_image_backends()
        
        # Initialize audio backends
        if self.config.get("enable_audio_generation", True):
            self._initialize_audio_backends()
        
        # Initialize video backends
        if self.config.get("enable_video_generation", False):
            self._initialize_video_backends()
        
        # Initialize text-to-speech backends
        if self.config.get("enable_text_to_speech", True):
            self._initialize_tts_backends()
        
        # Initialize speech-to-text backends
        if self.config.get("enable_speech_to_text", True):
            self._initialize_stt_backends()
        
        # Log available backends
        for media_type, backends in self.available_backends.items():
            if backends:
                logger.info(f"Available {media_type.value} backends: {', '.join(b['name'] for b in backends)}")
            else:
                logger.warning(f"No {media_type.value} backends available")
    
    def _initialize_image_backends(self):
        """Initialize available image generation backends"""
        backends = []
        
        # Try Stable Diffusion via Stability API
        try:
            if self.config.get("stability_api_key"):
                import requests
                
                # Test API key with a simple request
                headers = {
                    "Authorization": f"Bearer {self.config['stability_api_key']}",
                    "Content-Type": "application/json"
                }
                
                backends.append({
                    "name": "stability_api",
                    "description": "Stability.ai API (Stable Diffusion)",
                    "generate": self._generate_image_stability,
                    "supports_async": True,
                    "priority": 10
                })
                logger.info("Stable Diffusion via Stability API initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Stability API: {e}")
        
        # Try DALL-E via OpenAI API
        try:
            if self.config.get("openai_api_key"):
                import openai
                openai.api_key = self.config["openai_api_key"]
                
                backends.append({
                    "name": "dalle",
                    "description": "DALL-E via OpenAI API",
                    "generate": self._generate_image_dalle,
                    "supports_async": True,
                    "priority": 20
                })
                logger.info("DALL-E via OpenAI API initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize DALL-E API: {e}")
        
        # Try local Stable Diffusion
        try:
            # Check if diffusers library is installed
            import diffusers
            
            backends.append({
                "name": "stable_diffusion_local",
                "description": "Local Stable Diffusion",
                "generate": self._generate_image_sd_local,
                "supports_async": True,
                "priority": 30
            })
            logger.info("Local Stable Diffusion initialized")
        except ImportError:
            logger.info("Diffusers library not found, skipping local Stable Diffusion")
        except Exception as e:
            logger.warning(f"Failed to initialize local Stable Diffusion: {e}")
        
        # Try ComfyUI API if available
        try:
            import requests
            
            # Check if ComfyUI is running
            try:
                response = requests.get("http://127.0.0.1:8188/system_stats")
                if response.status_code == 200:
                    backends.append({
                        "name": "comfyui",
                        "description": "ComfyUI API",
                        "generate": self._generate_image_comfyui,
                        "supports_async": True,
                        "priority": 5  # High priority as it's likely the best local option
                    })
                    logger.info("ComfyUI API initialized")
            except:
                logger.info("ComfyUI not available at http://127.0.0.1:8188")
        except Exception as e:
            logger.warning(f"Failed to initialize ComfyUI API: {e}")
        
        # Sort backends by priority
        backends.sort(key=lambda x: x["priority"])
        self.available_backends[MediaType.IMAGE] = backends
    
    def _initialize_audio_backends(self):
        """Initialize available audio generation backends"""
        backends = []
        
        # Try Bark
        try:
            import transformers
            
            backends.append({
                "name": "bark",
                "description": "Bark text-to-audio by Suno",
                "generate": self._generate_audio_bark,
                "supports_async": True,
                "priority": 10
            })
            logger.info("Bark audio generation initialized")
        except ImportError:
            logger.info("Transformers library not found, skipping Bark audio generation")
        except Exception as e:
            logger.warning(f"Failed to initialize Bark: {e}")
        
        # Sort backends by priority
        backends.sort(key=lambda x: x["priority"])
        self.available_backends[MediaType.AUDIO] = backends
    
    def _initialize_video_backends(self):
        """Initialize available video generation backends"""
        backends = []
        
        # Try Stable Video Diffusion
        try:
            import diffusers
            
            backends.append({
                "name": "stable_video_diffusion",
                "description": "Stable Video Diffusion",
                "generate": self._generate_video_svd,
                "supports_async": True,
                "priority": 10
            })
            logger.info("Stable Video Diffusion initialized")
        except ImportError:
            logger.info("Diffusers library not found, skipping Stable Video Diffusion")
        except Exception as e:
            logger.warning(f"Failed to initialize Stable Video Diffusion: {e}")
        
        # Sort backends by priority
        backends.sort(key=lambda x: x["priority"])
        self.available_backends[MediaType.VIDEO] = backends
    
    def _initialize_tts_backends(self):
        """Initialize available text-to-speech backends"""
        backends = []
        
        # Try pyttsx3 (offline TTS)
        try:
            import pyttsx3
            
            # Test if it works
            engine = pyttsx3.init()
            
            backends.append({
                "name": "pyttsx3",
                "description": "Local text-to-speech via pyttsx3",
                "generate": self._generate_tts_pyttsx3,
                "supports_async": True,
                "priority": 20
            })
            logger.info("pyttsx3 text-to-speech initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3: {e}")
        
        # Try OpenAI TTS
        try:
            if self.config.get("openai_api_key"):
                import openai
                openai.api_key = self.config["openai_api_key"]
                
                backends.append({
                    "name": "openai_tts",
                    "description": "OpenAI text-to-speech API",
                    "generate": self._generate_tts_openai,
                    "supports_async": True,
                    "priority": 10
                })
                logger.info("OpenAI text-to-speech initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI TTS: {e}")
        
        # Sort backends by priority
        backends.sort(key=lambda x: x["priority"])
        self.available_backends[MediaType.TEXT_TO_SPEECH] = backends
    
    def _initialize_stt_backends(self):
        """Initialize available speech-to-text backends"""
        backends = []
        
        # Try WhisperX (local)
        try:
            import whisper
            
            backends.append({
                "name": "whisper",
                "description": "OpenAI Whisper (local)",
                "generate": self._generate_stt_whisper,
                "supports_async": True,
                "priority": 10
            })
            logger.info("Whisper speech-to-text initialized")
        except ImportError:
            logger.info("Whisper library not found, skipping local speech-to-text")
        except Exception as e:
            logger.warning(f"Failed to initialize Whisper: {e}")
        
        # Try SpeechRecognition with Google
        try:
            import speech_recognition as sr
            
            backends.append({
                "name": "google_speech",
                "description": "Google Speech Recognition API",
                "generate": self._generate_stt_google,
                "supports_async": True,
                "priority": 20
            })
            logger.info("Google Speech Recognition initialized")
        except ImportError:
            logger.info("SpeechRecognition library not found, skipping Google Speech")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Speech: {e}")
        
        # Sort backends by priority
        backends.sort(key=lambda x: x["priority"])
        self.available_backends[MediaType.SPEECH_TO_TEXT] = backends
    
    def get_media_path(self, media_type: MediaType, filename: Optional[str] = None) -> Path:
        """
        Get a path for saving media of a specific type
        
        Args:
            media_type: Type of media
            filename: Optional specific filename
            
        Returns:
            Path to save the media
        """
        # Create type-specific subdirectory
        media_subdir = self.media_dir / media_type.value
        media_subdir.mkdir(exist_ok=True, parents=True)
        
        if filename:
            return media_subdir / filename
        else:
            # Generate a timestamped filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
            
            if media_type == MediaType.IMAGE:
                return media_subdir / f"image_{timestamp}_{random_suffix}.png"
            elif media_type == MediaType.AUDIO:
                return media_subdir / f"audio_{timestamp}_{random_suffix}.mp3"
            elif media_type == MediaType.VIDEO:
                return media_subdir / f"video_{timestamp}_{random_suffix}.mp4"
            elif media_type == MediaType.TEXT_TO_SPEECH:
                return media_subdir / f"tts_{timestamp}_{random_suffix}.mp3"
            else:
                return media_subdir / f"media_{timestamp}_{random_suffix}.bin"
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                     width: int = 512, height: int = 512, **kwargs) -> Dict[str, Any]:
        """
        Generate an image based on a prompt
        
        Args:
            prompt: Text description of the desired image
            negative_prompt: Text description of what to avoid
            width: Image width in pixels
            height: Image height in pixels
            **kwargs: Additional arguments for the backend
            
        Returns:
            Dictionary with generation results
        """
        # Check if any backends are available
        if not self.available_backends[MediaType.IMAGE]:
            return {
                "success": False,
                "error": "No image generation backends available",
                "filepath": None
            }
        
        # Get preferred backend
        preferred = self.config.get("preferred_backends", {}).get("image")
        
        # Find the backend to use
        backend = None
        
        if preferred:
            # Find preferred backend if available
            for b in self.available_backends[MediaType.IMAGE]:
                if b["name"] == preferred:
                    backend = b
                    break
        
        # If preferred backend not found, use the first available
        if not backend and self.available_backends[MediaType.IMAGE]:
            backend = self.available_backends[MediaType.IMAGE][0]
        
        if not backend:
            return {
                "success": False,
                "error": "No image generation backends available",
                "filepath": None
            }
        
        try:
            # Prepare parameters
            params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                **kwargs
            }
            
            # Generate the image
            return backend["generate"](**params)
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def generate_audio(self, text: str, voice: str = "default", **kwargs) -> Dict[str, Any]:
        """
        Generate audio from text
        
        Args:
            text: Text to convert to audio
            voice: Voice identifier to use
            **kwargs: Additional arguments for the backend
            
        Returns:
            Dictionary with generation results
        """
        # Check if any backends are available
        if not self.available_backends[MediaType.AUDIO]:
            return {
                "success": False,
                "error": "No audio generation backends available",
                "filepath": None
            }
        
        # Get preferred backend
        preferred = self.config.get("preferred_backends", {}).get("audio")
        
        # Find the backend to use
        backend = None
        
        if preferred:
            # Find preferred backend if available
            for b in self.available_backends[MediaType.AUDIO]:
                if b["name"] == preferred:
                    backend = b
                    break
        
        # If preferred backend not found, use the first available
        if not backend and self.available_backends[MediaType.AUDIO]:
            backend = self.available_backends[MediaType.AUDIO][0]
        
        if not backend:
            return {
                "success": False,
                "error": "No audio generation backends available",
                "filepath": None
            }
        
        try:
            # Prepare parameters
            params = {
                "text": text,
                "voice": voice,
                **kwargs
            }
            
            # Generate the audio
            return backend["generate"](**params)
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def generate_video(self, prompt: str, duration_seconds: float = 3.0, **kwargs) -> Dict[str, Any]:
        """
        Generate a video based on a prompt
        
        Args:
            prompt: Text description of the desired video
            duration_seconds: Duration of the video in seconds
            **kwargs: Additional arguments for the backend
            
        Returns:
            Dictionary with generation results
        """
        # Check if any backends are available
        if not self.available_backends[MediaType.VIDEO]:
            return {
                "success": False,
                "error": "No video generation backends available",
                "filepath": None
            }
        
        # Get preferred backend
        preferred = self.config.get("preferred_backends", {}).get("video")
        
        # Find the backend to use
        backend = None
        
        if preferred:
            # Find preferred backend if available
            for b in self.available_backends[MediaType.VIDEO]:
                if b["name"] == preferred:
                    backend = b
                    break
        
        # If preferred backend not found, use the first available
        if not backend and self.available_backends[MediaType.VIDEO]:
            backend = self.available_backends[MediaType.VIDEO][0]
        
        if not backend:
            return {
                "success": False,
                "error": "No video generation backends available",
                "filepath": None
            }
        
        try:
            # Prepare parameters
            params = {
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                **kwargs
            }
            
            # Generate the video
            return backend["generate"](**params)
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def text_to_speech(self, text: str, voice: str = "default", **kwargs) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier to use
            **kwargs: Additional arguments for the backend
            
        Returns:
            Dictionary with generation results
        """
        # Check if any backends are available
        if not self.available_backends[MediaType.TEXT_TO_SPEECH]:
            return {
                "success": False,
                "error": "No text-to-speech backends available",
                "filepath": None
            }
        
        # Get preferred backend
        preferred = self.config.get("preferred_backends", {}).get("text_to_speech")
        
        # Find the backend to use
        backend = None
        
        if preferred:
            # Find preferred backend if available
            for b in self.available_backends[MediaType.TEXT_TO_SPEECH]:
                if b["name"] == preferred:
                    backend = b
                    break
        
        # If preferred backend not found, use the first available
        if not backend and self.available_backends[MediaType.TEXT_TO_SPEECH]:
            backend = self.available_backends[MediaType.TEXT_TO_SPEECH][0]
        
        if not backend:
            return {
                "success": False,
                "error": "No text-to-speech backends available",
                "filepath": None
            }
        
        try:
            # Prepare parameters
            params = {
                "text": text,
                "voice": voice,
                **kwargs
            }
            
            # Generate the speech
            return backend["generate"](**params)
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def speech_to_text(self, audio_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """
        Convert speech to text
        
        Args:
            audio_path: Path to the audio file
            **kwargs: Additional arguments for the backend
            
        Returns:
            Dictionary with transcription results
        """
        # Check if any backends are available
        if not self.available_backends[MediaType.SPEECH_TO_TEXT]:
            return {
                "success": False,
                "error": "No speech-to-text backends available",
                "text": None
            }
        
        # Get preferred backend
        preferred = self.config.get("preferred_backends", {}).get("speech_to_text")
        
        # Find the backend to use
        backend = None
        
        if preferred:
            # Find preferred backend if available
            for b in self.available_backends[MediaType.SPEECH_TO_TEXT]:
                if b["name"] == preferred:
                    backend = b
                    break
        
        # If preferred backend not found, use the first available
        if not backend and self.available_backends[MediaType.SPEECH_TO_TEXT]:
            backend = self.available_backends[MediaType.SPEECH_TO_TEXT][0]
        
        if not backend:
            return {
                "success": False,
                "error": "No speech-to-text backends available",
                "text": None
            }
        
        try:
            # Prepare parameters
            params = {
                "audio_path": audio_path,
                **kwargs
            }
            
            # Transcribe the speech
            return backend["generate"](**params)
        except Exception as e:
            logger.error(f"Error converting speech to text: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }
    
    def generate_async(self, media_type: MediaType, **kwargs) -> str:
        """
        Schedule asynchronous media generation
        
        Args:
            media_type: Type of media to generate
            **kwargs: Parameters for the generation function
            
        Returns:
            Task ID for tracking the generation
        """
        # Generate a unique task ID
        task_id = f"{media_type.value}_{time.strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        
        # Add the task to the queue
        self.task_queue.put({
            "task_id": task_id,
            "media_type": media_type,
            "params": kwargs,
            "status": "queued",
            "timestamp": time.time()
        })
        
        # Initialize task tracking
        self.active_tasks[task_id] = {
            "status": "queued",
            "progress": 0.0,
            "result": None,
            "error": None,
            "timestamp": time.time()
        }
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of an asynchronous task
        
        Args:
            task_id: Task ID from generate_async
            
        Returns:
            Dictionary with task status information
        """
        if task_id not in self.active_tasks:
            return {
                "status": "unknown",
                "error": "Task not found"
            }
        
        return self.active_tasks[task_id]
    
    def get_available_backends(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get information about available backends
        
        Returns:
            Dictionary mapping media types to lists of backend info
        """
        result = {}
        
        for media_type, backends in self.available_backends.items():
            result[media_type.value] = [
                {"name": b["name"], "description": b["description"]} 
                for b in backends
            ]
        
        return result
    
    def _worker(self):
        """Background worker for asynchronous media generation"""
        while True:
            try:
                # Get task from the queue
                task = self.task_queue.get()
                
                # Skip if the task is None (shutdown signal)
                if task is None:
                    break
                
                task_id = task["task_id"]
                media_type = task["media_type"]
                params = task["params"]
                
                # Update task status
                self.active_tasks[task_id]["status"] = "processing"
                
                try:
                    # Call the appropriate generation function
                    if media_type == MediaType.IMAGE:
                        result = self.generate_image(**params)
                    elif media_type == MediaType.AUDIO:
                        result = self.generate_audio(**params)
                    elif media_type == MediaType.VIDEO:
                        result = self.generate_video(**params)
                    elif media_type == MediaType.TEXT_TO_SPEECH:
                        result = self.text_to_speech(**params)
                    elif media_type == MediaType.SPEECH_TO_TEXT:
                        result = self.speech_to_text(**params)
                    else:
                        raise ValueError(f"Unknown media type: {media_type}")
                    
                    # Update task status
                    if result.get("success", False):
                        self.active_tasks[task_id]["status"] = "completed"
                        self.active_tasks[task_id]["progress"] = 1.0
                        self.active_tasks[task_id]["result"] = result
                    else:
                        self.active_tasks[task_id]["status"] = "failed"
                        self.active_tasks[task_id]["error"] = result.get("error", "Unknown error")
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {e}")
                    self.active_tasks[task_id]["status"] = "failed"
                    self.active_tasks[task_id]["error"] = str(e)
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Clean up old completed/failed tasks
                self._clean_old_tasks()
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
    
    def _clean_old_tasks(self, max_age_seconds: int = 3600):
        """Clean up old completed/failed tasks"""
        current_time = time.time()
        
        # Find tasks to remove
        tasks_to_remove = []
        for task_id, task in self.active_tasks.items():
            if task["status"] in ["completed", "failed"] and current_time - task["timestamp"] > max_age_seconds:
                tasks_to_remove.append(task_id)
        
        # Remove tasks
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
    
    # Image generation backend implementations
    def _generate_image_stability(self, prompt: str, negative_prompt: str = "", 
                               width: int = 512, height: int = 512, **kwargs) -> Dict[str, Any]:
        """Generate image using Stability API"""
        import requests
        import json
        import base64
        
        output_path = self.get_media_path(MediaType.IMAGE)
        
        try:
            # Prepare API request
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.config['stability_api_key']}"
            }
            
            body = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": kwargs.get("cfg_scale", 7.0),
                "height": height,
                "width": width,
                "samples": 1,
                "steps": kwargs.get("steps", 30),
            }
            
            if negative_prompt:
                body["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
            
            # Send request
            response = requests.post(url, headers=headers, json=body)
            
            if response.status_code != 200:
                logger.error(f"Stability API error: {response.text}")
                return {
                    "success": False,
                    "error": f"API returned {response.status_code}: {response.text}",
                    "filepath": None
                }
            
            # Parse response
            data = response.json()
            
            if "artifacts" not in data or not data["artifacts"]:
                return {
                    "success": False,
                    "error": "No image generated",
                    "filepath": None
                }
            
            # Save the image
            for i, image in enumerate(data["artifacts"]):
                image_data = base64.b64decode(image["base64"])
                
                # Save the image
                with open(output_path, "wb") as f:
                    f.write(image_data)
                
                # Only use the first image for now
                break
            
            return {
                "success": True,
                "filepath": str(output_path),
                "prompt": prompt,
                "backend": "stability_api"
            }
        except Exception as e:
            logger.error(f"Error generating image with Stability API: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def _generate_image_dalle(self, prompt: str, negative_prompt: str = "", 
                           width: int = 1024, height: int = 1024, **kwargs) -> Dict[str, Any]:
        """Generate image using DALL-E via OpenAI API"""
        import openai
        import requests
        
        output_path = self.get_media_path(MediaType.IMAGE)
        
        try:
            openai.api_key = self.config["openai_api_key"]
            
            # Determine size
            if width == height:
                if width <= 512:
                    size = "256x256"
                elif width <= 768:
                    size = "512x512"
                else:
                    size = "1024x1024"
            else:
                # DALL-E 3 supports these sizes
                if (width, height) in [(1024, 1792), (1792, 1024)]:
                    size = f"{width}x{height}"
                else:
                    # Default to square
                    size = "1024x1024"
            
            # Generate the image
            response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=kwargs.get("quality", "standard"),
                n=1
            )
            
            # Download the image
            image_url = response["data"][0]["url"]
            image_response = requests.get(image_url)
            
            # Save the image
            with open(output_path, "wb") as f:
                f.write(image_response.content)
            
            return {
                "success": True,
                "filepath": str(output_path),
                "prompt": prompt,
                "backend": "dalle"
            }
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def _generate_image_sd_local(self, prompt: str, negative_prompt: str = "", 
                              width: int = 512, height: int = 512, **kwargs) -> Dict[str, Any]:
        """Generate image using local Stable Diffusion"""
        import torch
        from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
        
        output_path = self.get_media_path(MediaType.IMAGE)
        
        try:
            # Load the pipeline
            model_id = "stabilityai/stable-diffusion-2-1"
            
            # Use DPMSolver++ scheduler for faster inference
            pipe = StableDiffusionPipeline.from_pretrained(model_id)
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            
            # Use GPU if available
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            
            # Generate the image
            image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=kwargs.get("steps", 25),
                guidance_scale=kwargs.get("cfg_scale", 7.5)
            ).images[0]
            
            # Save the image
            image.save(output_path)
            
            return {
                "success": True,
                "filepath": str(output_path),
                "prompt": prompt,
                "backend": "stable_diffusion_local"
            }
        except Exception as e:
            logger.error(f"Error generating image with local Stable Diffusion: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def _generate_image_comfyui(self, prompt: str, negative_prompt: str = "", 
                             width: int = 512, height: int = 512, **kwargs) -> Dict[str, Any]:
        """Generate image using ComfyUI API"""
        import requests
        import json
        import websocket
        import uuid
        import base64
        
        output_path = self.get_media_path(MediaType.IMAGE)
        
        try:
            # Simple ComfyUI workflow for text-to-image
            workflow = {
                "3": {
                    "inputs": {
                        "seed": kwargs.get("seed", 0),
                        "steps": kwargs.get("steps", 20),
                        "cfg": kwargs.get("cfg_scale", 8.0),
                        "sampler_name": "euler_ancestral",
                        "scheduler": "karras",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0]
                    },
                    "class_type": "KSampler"
                },
                "4": {
                    "inputs": {
                        "ckpt_name": "dreamshaper_8.safetensors"
                    },
                    "class_type": "CheckpointLoaderSimple"
                },
                "5": {
                    "inputs": {
                        "width": width,
                        "height": height,
                        "batch_size": 1
                    },
                    "class_type": "EmptyLatentImage"
                },
                "6": {
                    "inputs": {
                        "text": prompt,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "7": {
                    "inputs": {
                        "text": negative_prompt,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "8": {
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    },
                    "class_type": "VAEDecode"
                },
                "9": {
                    "inputs": {
                        "filename_prefix": "ComfyUI",
                        "images": ["8", 0]
                    },
                    "class_type": "SaveImage"
                }
            }
            
            # Generate prompt ID
            prompt_id = str(uuid.uuid4())
            
            # Send the workflow to ComfyUI
            url = "http://127.0.0.1:8188/prompt"
            
            response = requests.post(
                url,
                json={
                    "prompt": workflow,
                    "client_id": prompt_id
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"ComfyUI API returned {response.status_code}: {response.text}",
                    "filepath": None
                }
            
            # Connect to websocket to monitor progress
            ws = websocket.WebSocket()
            ws.connect("ws://127.0.0.1:8188/ws")
            
            # Wait for the image to be generated
            while True:
                msg = json.loads(ws.recv())
                
                if msg["type"] == "executing":
                    node_id = msg["data"]["node"]
                    
                    if node_id == "9":  # SaveImage node
                        # Image is saved, get the filename
                        output_images = requests.get("http://127.0.0.1:8188/history").json()
                        
                        if prompt_id in output_images:
                            image_data = output_images[prompt_id]["outputs"]["9"]["images"][0]
                            image_filename = image_data["filename"]
                            
                            # Download the image
                            image_response = requests.get(f"http://127.0.0.1:8188/view?filename={image_filename}")
                            
                            # Save the image
                            with open(output_path, "wb") as f:
                                f.write(image_response.content)
                            
                            return {
                                "success": True,
                                "filepath": str(output_path),
                                "prompt": prompt,
                                "backend": "comfyui"
                            }
                
                elif msg["type"] == "error":
                    return {
                        "success": False,
                        "error": f"ComfyUI error: {msg['data']['message']}",
                        "filepath": None
                    }
        except Exception as e:
            logger.error(f"Error generating image with ComfyUI: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    # Audio generation backend implementations
    def _generate_audio_bark(self, text: str, voice: str = "default", **kwargs) -> Dict[str, Any]:
        """Generate audio using Bark"""
        from transformers import BarkModel, BarkProcessor
        import torch
        import scipy.io.wavfile
        
        output_path = self.get_media_path(MediaType.AUDIO)
        
        try:
            # Initialize model and processor
            model = BarkModel.from_pretrained("suno/bark")
            processor = BarkProcessor.from_pretrained("suno/bark")
            
            # Use GPU if available
            if torch.cuda.is_available():
                model = model.to("cuda")
            
            # Map voice to bark speaker
            if voice == "default" or voice == "male":
                speaker = "v2/en_speaker_6"
            elif voice == "female":
                speaker = "v2/en_speaker_9"
            else:
                # Try to use the voice as a direct speaker ID
                speaker = voice
            
            # Prepare inputs
            inputs = processor(text, voice_preset=speaker)
            
            # Generate audio
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
            output = model.generate(**inputs)
            audio_array = output[0].cpu().numpy()
            
            # Get the sample rate
            sample_rate = model.generation_config.sample_rate
            
            # Save as wav
            temp_path = output_path.with_suffix('.wav')
            scipy.io.wavfile.write(temp_path, rate=sample_rate, data=audio_array)
            
            # Convert to mp3 if possible
            try:
                import ffmpeg
                
                # Convert wav to mp3
                ffmpeg.input(str(temp_path)).output(str(output_path)).run(quiet=True, overwrite_output=True)
                
                # Delete temporary wav file
                os.remove(temp_path)
            except:
                # If conversion fails, use the wav file directly
                output_path = temp_path
            
            return {
                "success": True,
                "filepath": str(output_path),
                "text": text,
                "backend": "bark"
            }
        except Exception as e:
            logger.error(f"Error generating audio with Bark: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    # Video generation backend implementations
    def _generate_video_svd(self, prompt: str, duration_seconds: float = 3.0, **kwargs) -> Dict[str, Any]:
        """Generate video using Stable Video Diffusion"""
        import torch
        from diffusers import StableVideoDiffusionPipeline
        from diffusers.utils import export_to_video
        
        output_path = self.get_media_path(MediaType.VIDEO)
        
        try:
            # Load the pipeline
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid-xt",
                torch_dtype=torch.float16,
                variant="fp16"
            )
            
            # Use GPU if available
            if torch.cuda.is_available():
                pipe = pipe.to("cuda")
            
            # First generate a still image if none provided
            conditioning_image = kwargs.get("conditioning_image")
            
            if conditioning_image is None:
                # Generate an image first using our image generation
                image_result = self.generate_image(prompt=prompt)
                
                if not image_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to generate conditioning image: {image_result['error']}",
                        "filepath": None
                    }
                
                # Load the generated image
                from PIL import Image
                conditioning_image = Image.open(image_result["filepath"])
            elif isinstance(conditioning_image, str):
                # Load the image from the provided path
                from PIL import Image
                conditioning_image = Image.open(conditioning_image)
            
            # Determine number of frames based on duration
            # Default is 25 frames = ~3 seconds at 8 fps
            num_frames = min(int(duration_seconds * 8), 60)
            
            # Generate the video frames
            frames = pipe(
                prompt=prompt,
                conditioning_image=conditioning_image,
                num_frames=num_frames,
                num_inference_steps=kwargs.get("steps", 25),
                guidance_scale=kwargs.get("guidance_scale", 7.5),
                fps=8
            ).frames[0]
            
            # Save as temporary frames
            temp_frames_dir = Path("temp_frames")
            temp_frames_dir.mkdir(exist_ok=True)
            
            # Save each frame
            frame_paths = []
            for i, frame in enumerate(frames):
                frame_path = temp_frames_dir / f"frame_{i:04d}.png"
                frame.save(frame_path)
                frame_paths.append(frame_path)
            
            # Export to video
            temp_video_path = export_to_video(frame_paths, output_path)
            
            # Clean up temporary frames
            for frame_path in frame_paths:
                os.remove(frame_path)
            if temp_frames_dir.exists():
                temp_frames_dir.rmdir()
            
            return {
                "success": True,
                "filepath": str(output_path),
                "prompt": prompt,
                "backend": "stable_video_diffusion"
            }
        except Exception as e:
            logger.error(f"Error generating video with Stable Video Diffusion: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    # Text-to-speech backend implementations
    def _generate_tts_pyttsx3(self, text: str, voice: str = "default", **kwargs) -> Dict[str, Any]:
        """Generate speech using pyttsx3"""
        import pyttsx3
        
        output_path = self.get_media_path(MediaType.TEXT_TO_SPEECH)
        
        try:
            # Initialize the TTS engine
            engine = pyttsx3.init()
            
            # Set voice properties
            if voice != "default":
                # Get available voices
                voices = engine.getProperty('voices')
                
                # Default to first voice
                target_voice = voices[0].id
                
                # Try to find a matching voice
                for v in voices:
                    if (voice.lower() in v.name.lower() or 
                        voice.lower() in v.id.lower() or
                        (voice.lower() == "male" and "male" in v.gender.lower()) or
                        (voice.lower() == "female" and "female" in v.gender.lower())):
                        target_voice = v.id
                        break
                
                # Set the voice
                engine.setProperty('voice', target_voice)
            
            # Set rate (speed)
            if "rate" in kwargs:
                engine.setProperty('rate', kwargs["rate"])
            
            # Set volume
            if "volume" in kwargs:
                engine.setProperty('volume', kwargs["volume"])
            
            # Save to file
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            
            return {
                "success": True,
                "filepath": str(output_path),
                "text": text,
                "backend": "pyttsx3"
            }
        except Exception as e:
            logger.error(f"Error generating speech with pyttsx3: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def _generate_tts_openai(self, text: str, voice: str = "default", **kwargs) -> Dict[str, Any]:
        """Generate speech using OpenAI TTS API"""
        import openai
        
        output_path = self.get_media_path(MediaType.TEXT_TO_SPEECH)
        
        try:
            openai.api_key = self.config["openai_api_key"]
            
            # Map voice
            if voice == "default" or voice == "male":
                openai_voice = "onyx"
            elif voice == "female":
                openai_voice = "nova"
            elif voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
                openai_voice = voice
            else:
                openai_voice = "onyx"  # Default to this voice
            
            # Generate speech
            response = openai.audio.speech.create(
                model="tts-1",
                voice=openai_voice,
                input=text
            )
            
            # Save to file
            response.stream_to_file(str(output_path))
            
            return {
                "success": True,
                "filepath": str(output_path),
                "text": text,
                "backend": "openai_tts"
            }
        except Exception as e:
            logger.error(f"Error generating speech with OpenAI TTS: {e}")
            return {
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    # Speech-to-text backend implementations
    def _generate_stt_whisper(self, audio_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Generate text from speech using Whisper"""
        import whisper
        
        try:
            # Convert audio_path to string if it's a Path
            audio_path = str(audio_path)
            
            # Load Whisper model
            model_size = kwargs.get("model_size", "base")
            model = whisper.load_model(model_size)
            
            # Transcribe audio
            result = model.transcribe(audio_path)
            
            return {
                "success": True,
                "text": result["text"],
                "audio_path": audio_path,
                "backend": "whisper"
            }
        except Exception as e:
            logger.error(f"Error transcribing speech with Whisper: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }
    
    def _generate_stt_google(self, audio_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Generate text from speech using Google Speech Recognition"""
        import speech_recognition as sr
        
        try:
            # Initialize recognizer
            recognizer = sr.Recognizer()
            
            # Convert audio_path to string if it's a Path
            audio_path = str(audio_path)
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            
            # Recognize speech
            text = recognizer.recognize_google(audio_data)
            
            return {
                "success": True,
                "text": text,
                "audio_path": audio_path,
                "backend": "google_speech"
            }
        except Exception as e:
            logger.error(f"Error transcribing speech with Google Speech: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of MediaGenerator"""
    global _instance
    if _instance is None:
        _instance = MediaGenerator()
    return _instance

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Test the media generator
    generator = get_instance()
    
    # Print available backends
    backends = generator.get_available_backends()
    print("\nAvailable backends:")
    for media_type, available_backends in backends.items():
        print(f"  {media_type}:")
        for backend in available_backends:
            print(f"    - {backend['name']}: {backend['description']}")
    
    # Test image generation
    if backends.get(MediaType.IMAGE.value):
        print("\nTesting image generation...")
        result = generator.generate_image(
            prompt="A serene landscape with mountains and a lake",
            width=512,
            height=512
        )
        
        if result["success"]:
            print(f"Image generated: {result['filepath']}")
        else:
            print(f"Image generation failed: {result['error']}")
    
    # Test text-to-speech
    if backends.get(MediaType.TEXT_TO_SPEECH.value):
        print("\nTesting text-to-speech...")
        result = generator.text_to_speech(
            text="Hello, this is a test of the text-to-speech functionality."
        )
        
        if result["success"]:
            print(f"Speech generated: {result['filepath']}")
        else:
            print(f"Speech generation failed: {result['error']}")
