import logging
import json
import os
import time
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class MediaIntegrator:
    """
    Unified media integration manager that handles various media generation capabilities.
    """
    
    def __init__(self, config_path=None):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize generation providers
        self.providers = {
            "vision": self._init_vision_provider(),
            "image": self._init_image_provider(),
            "video": self._init_video_provider(),
            "3d": self._init_3d_provider(),
            "speech": self._init_speech_provider()
        }
        
        # Cache directory for generated media
        self.cache_dir = Path(self.config.get("cache_dir", "generated"))
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize media detection patterns
        self._init_detection_patterns()
        
        logger.info(f"Media integrator initialized with providers: {', '.join(self.providers.keys())}")
    
    def _load_config(self, config_path=None) -> Dict[str, Any]:
        """Load configuration from disk or use defaults."""
        default_config = {
            "cache_dir": "generated",
            "cache_expiry_days": 7,
            "image": {
                "enabled": True,
                "nsfw_allowed": False,
                "default_size": 1024,
                "default_steps": 30
            },
            "video": {
                "enabled": True,
                "provider": "comfyui",
                "max_duration": 10
            },
            "3d": {
                "enabled": True,
                "default_complexity": "medium"
            },
            "vision": {
                "enabled": True
            },
            "speech": {
                "enabled": True
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config.get(key), dict):
                        # Merge nested dicts
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                
                logger.info(f"Loaded media integration config from {config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        logger.info("Using default media integration config")
        return default_config
    
    def _init_detection_patterns(self):
        """Initialize regex patterns for detecting media generation requests."""
        self.detection_patterns = {
            "image": [
                r"(?i)(create|generate|make)\s+(?:an?|the)\s+image\s+(?:of|showing|with)\s+(.*)",
                r"(?i)(draw|show|display|create)\s+(?:a picture|an image|a photo)\s+(?:of|showing|with)\s+(.*)",
                r"(?i)(visualize|illustrate)\s+(.*)"
            ],
            "video": [
                r"(?i)(create|generate|make)\s+(?:a|the)\s+video\s+(?:of|showing|with)\s+(.*)",
                r"(?i)(animate|create animation|show animation)\s+(?:of|showing|with)\s+(.*)"
            ],
            "3d": [
                r"(?i)(create|generate|make)\s+(?:a|the)\s+3[dD]\s+model\s+(?:of|showing|with)\s+(.*)",
                r"(?i)(model|show|display|create)\s+(?:in|as)\s+3[dD]\s+(.*)"
            ]
        }
    
    def _init_vision_provider(self):
        """Initialize the vision (image understanding) provider."""
        if not self.config.get("vision", {}).get("enabled", True):
            return None
            
        try:
            from modules.phi4_integration import Phi4MultimodalIntegration
            vision_provider = Phi4MultimodalIntegration()
            
            if vision_provider.is_available:
                logger.info("Vision provider (Phi-4) initialized successfully")
                return vision_provider
            else:
                logger.warning("Vision provider (Phi-4) initialization failed")
                return None
        except ImportError:
            logger.warning("Phi4MultimodalIntegration module not found")
            return None
        except Exception as e:
            logger.error(f"Error initializing vision provider: {e}")
            return None
    
    def _init_image_provider(self):
        """Initialize the image generation provider."""
        if not self.config.get("image", {}).get("enabled", True):
            return None
            
        try:
            from modules.flux_integration import FluxImageGenerator
            image_provider = FluxImageGenerator()
            
            if image_provider.is_available:
                logger.info("Image provider (FLUX) initialized successfully")
                return image_provider
            else:
                logger.warning("Image provider (FLUX) initialization failed")
                return None
        except ImportError:
            logger.warning("FluxImageGenerator module not found")
            return None
        except Exception as e:
            logger.error(f"Error initializing image provider: {e}")
            return None
    
    def _init_video_provider(self):
        """Initialize the video generation provider."""
        if not self.config.get("video", {}).get("enabled", True):
            return None
            
        # In a real implementation, you would initialize a video generation provider here
        logger.info("Video provider placeholder initialized (not yet implemented)")
        return {"status": "placeholder"}
    
    def _init_3d_provider(self):
        """Initialize the 3D model generation provider."""
        if not self.config.get("3d", {}).get("enabled", True):
            return None
            
        try:
            from modules.cube_integration import Cube3DGenerator
            model_provider = Cube3DGenerator()
            
            if model_provider.is_available:
                logger.info("3D model provider (Cube) initialized successfully")
                return model_provider
            else:
                logger.warning("3D model provider (Cube) initialization failed")
                return None
        except ImportError:
            logger.warning("Cube3DGenerator module not found")
            return None
        except Exception as e:
            logger.error(f"Error initializing 3D model provider: {e}")
            return None
    
    def _init_speech_provider(self):
        """Initialize the speech recognition and synthesis provider."""
        if not self.config.get("speech", {}).get("enabled", True):
            return None
            
        try:
            # For now, we'll use the same Phi4 provider for speech
            from modules.phi4_integration import Phi4MultimodalIntegration
            speech_provider = Phi4MultimodalIntegration()
            
            if speech_provider.is_available:
                logger.info("Speech provider (Phi-4) initialized successfully")
                return speech_provider
            else:
                logger.warning("Speech provider (Phi-4) initialization failed")
                return None
        except ImportError:
            logger.warning("Phi4MultimodalIntegration module not found")
            return None
        except Exception as e:
            logger.error(f"Error initializing speech provider: {e}")
            return None
    
    def get_media_response(self, message: str) -> Dict[str, Any]:
        """
        Analyze a message to check if it's requesting media generation.
        
        Args:
            message: The user message to analyze
            
        Returns:
            Dict with information about detected media request, if any
        """
        result = {
            "has_media": False,
            "media_type": None,
            "media_prompt": None,
            "response_text": None,
            "media_path": None
        }
        
        # Check if any of our patterns match
        for media_type, patterns in self.detection_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    prompt = match.group(2).strip() if len(match.groups()) > 1 else message
                    
                    # Check if the provider is available
                    provider_key = "image" if media_type == "image" else "3d" if media_type == "3d" else "video"
                    if self.providers.get(provider_key) is None:
                        result["has_media"] = True
                        result["media_type"] = media_type
                        result["media_prompt"] = prompt
                        result["response_text"] = f"I'd like to generate a {media_type} for you, but the {media_type} generation capability is not available."
                        return result
                    
                    # Generate the requested media
                    media_result = self.generate_media({
                        "type": media_type,
                        "prompt": prompt,
                        "detected": True
                    })
                    
                    if media_result.get("success", False):
                        result["has_media"] = True
                        result["media_type"] = media_type
                        result["media_prompt"] = prompt
                        result["media_path"] = media_result.get("path")
                        result["response_text"] = f"I've generated a {media_type} based on your request: \"{prompt}\""
                        if media_type == "image" and media_result.get("seed"):
                            result["response_text"] += f"\n\nSeed: {media_result['seed']}"
                    else:
                        result["has_media"] = True
                        result["media_type"] = media_type
                        result["media_prompt"] = prompt
                        result["response_text"] = f"I tried to generate a {media_type} for you, but encountered an error: {media_result.get('error', 'unknown error')}"
                    
                    return result
        
        # No media request detected
        return result
    
    def generate_media(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate media based on the request.
        
        Args:
            request: Dictionary with request details including:
                    - type: "image", "video", or "3d"
                    - prompt: Text prompt for generation
                    - params: Optional parameters specific to the media type
                    
        Returns:
            Dict with generation results
        """
        media_type = request.get("type")
        prompt = request.get("prompt")
        params = request.get("params", {})
        
        if not prompt:
            return {
                "success": False,
                "error": "No prompt provided for media generation"
            }
        
        if media_type == "image":
            return self._generate_image(prompt, params)
        elif media_type == "video":
            return self._generate_video(prompt, params)
        elif media_type == "3d":
            return self._generate_3d_model(prompt, params)
        else:
            return {
                "success": False,
                "error": f"Unsupported media type: {media_type}"
            }
    
    def _generate_image(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the configured provider."""
        if not self.providers.get("image"):
            return {
                "success": False,
                "error": "Image generation provider not available"
            }
        
        try:
            # Get image configuration
            image_config = self.config.get("image", {})
            
            # Extract parameters with defaults from config
            width = params.get("width", params.get("size", image_config.get("default_size", 1024)))
            height = params.get("height", params.get("size", image_config.get("default_size", 1024)))
            steps = params.get("steps", image_config.get("default_steps", 30))
            guidance_scale = params.get("guidance_scale", params.get("cfg_scale", 7.5))
            negative_prompt = params.get("negative_prompt", "")
            seed = params.get("seed")
            nsfw_allowed = params.get("nsfw_allowed", image_config.get("nsfw_allowed", False))
            
            # Generate the image
            result = self.providers["image"].generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                guidance_scale=guidance_scale,
                nsfw_allowed=nsfw_allowed,
                seed=seed
            )
            
            # If successful, add type to result
            if result.get("success", False):
                result["type"] = "image"
                
            return result
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "image"
            }
    
    def _generate_video(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a video using the configured provider."""
        if not self.providers.get("video"):
            return {
                "success": False,
                "error": "Video generation provider not available"
            }
        
        # This is a placeholder - in a real implementation, you would call the video provider
        logger.info(f"Video generation requested: {prompt}")
        
        return {
            "success": False,
            "error": "Video generation not yet implemented",
            "type": "video"
        }
    
    def _generate_3d_model(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a 3D model using the configured provider."""
        if not self.providers.get("3d"):
            return {
                "success": False,
                "error": "3D model generation provider not available"
            }
        
        try:
            # Get 3D configuration
            model_config = self.config.get("3d", {})
            
            # Extract parameters with defaults from config
            complexity = params.get("complexity", model_config.get("default_complexity", "medium"))
            output_format = params.get("format", "glb")
            texture = params.get("texture", "detailed")
            seed = params.get("seed")
            
            # Generate the 3D model
            result = self.providers["3d"].generate_3d_model(
                prompt=prompt,
                complexity=complexity,
                output_format=output_format,
                texture=texture,
                seed=seed
            )
            
            # If successful, add type to result
            if result.get("success", False):
                result["type"] = "3d"
                
            return result
            
        except Exception as e:
            logger.error(f"Error generating 3D model: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "3d"
            }
    
    def process_image(self, image_path: Union[str, Path], prompt: str = None) -> str:
        """
        Process an image using vision capabilities.
        
        Args:
            image_path: Path to the image file
            prompt: Optional prompt to guide the processing
            
        Returns:
            String response describing or analyzing the image
        """
        if not self.providers.get("vision"):
            return "Image processing capability is not available."
        
        try:
            # Process the image
            if prompt:
                return self.providers["vision"].process_image(image_path, prompt)
            else:
                return self.providers["vision"].process_image(image_path)
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"Error processing image: {str(e)}"
    
    def ocr_image(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        if not self.providers.get("vision"):
            return "OCR capability is not available."
        
        try:
            return self.providers["vision"].ocr_image(image_path)
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return f"Error extracting text: {str(e)}"
    
    def transcribe_speech(self, audio_path: Union[str, Path]) -> str:
        """
        Transcribe speech from an audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if not self.providers.get("speech"):
            return "Speech transcription capability is not available."
        
        try:
            return self.providers["speech"].transcribe_speech(audio_path)
        except Exception as e:
            logger.error(f"Error transcribing speech: {e}")
            return f"Error transcribing speech: {str(e)}"
    
    def text_to_speech(self, text: str, output_path: Optional[Union[str, Path]] = None) -> Union[str, bytes]:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save the audio file
            
        Returns:
            Path to the generated audio file or the audio data
        """
        if not self.providers.get("speech"):
            return "Text-to-speech capability is not available."
        
        try:
            return self.providers["speech"].text_to_speech(text, output_path)
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return f"Error generating speech: {str(e)}"

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import time
import random

# Configure logging
logger = logging.getLogger(__name__)

class MediaIntegrator:
    """
    Integrates various media generation capabilities.
    Manages interfaces to FLUX (image), ComfyUI (video), Phi-4 (vision), and Cube (3D).
    """
    
    def __init__(self, options=None):
        """
        Initialize media integration interfaces.
        
        Args:
            options (dict): Optional dictionary of feature flags to control which 
                            capabilities are enabled
        """
        # Set default options
        self.options = {
            "enable_image_gen": True,
            "enable_video_gen": True,
            "enable_3d_gen": True,
            "enable_vision": True,
            "enable_speech": True
        }
        
        # Update with provided options
        if options:
            self.options.update(options)
            
        # Initialize capabilities with lazy loading - only create instances when first used
        self._capabilities = {
            "image": {"available": False, "instance": None, "name": "FLUX Image Generator"},
            "video": {"available": False, "instance": None, "name": "ComfyUI Video Generator"},
            "vision": {"available": False, "instance": None, "name": "Phi-4 Vision Processor"},
            "speech": {"available": False, "instance": None, "name": "Phi-4 Speech Processor"},
            "3d": {"available": False, "instance": None, "name": "Cube 3D Generator"}
        }
        
        # Check availability of each feature based on options
        if self.options.get("enable_image_gen", True):
            self._capabilities["image"]["available"] = self._check_flux_available()
            
        if self.options.get("enable_video_gen", True):
            self._capabilities["video"]["available"] = self._check_comfyui_available()
            
        if self.options.get("enable_vision", True) or self.options.get("enable_speech", True):
            phi4_available = self._check_phi4_available()
            self._capabilities["vision"]["available"] = phi4_available and self.options.get("enable_vision", True)
            self._capabilities["speech"]["available"] = phi4_available and self.options.get("enable_speech", True)
            
        if self.options.get("enable_3d_gen", True):
            self._capabilities["3d"]["available"] = self._check_cube_available()
        
        # Log available capabilities
        available = [k for k, v in self._capabilities.items() if v["available"]]
        logger.info(f"Media integrator initialized with capabilities: {', '.join(available)}")
    
    @property
    def capabilities(self):
        """Get the capabilities with lazy loading."""
        return self._capabilities
    
    def _check_phi4_available(self) -> bool:
        """Check if Phi-4 multimodal model is available."""
        phi4_path = Path("G:/AI/Lyra/BigModes/Phi-4-multimodal-instruct-abliterated")
        model_files_exist = all(
            [phi4_path.exists(),
             (phi4_path / "model-00001-of-00003.safetensors").exists()]
        )
        return model_files_exist
    
    def _check_flux_available(self) -> bool:
        """Check if FLUX image generation is available."""
        flux_path = Path("G:/AI/Full Models/FLUX.1-dev")
        return flux_path.exists() and (flux_path / "model_index.json").exists()
    
    def _check_comfyui_available(self) -> bool:
        """Check if ComfyUI is available for video generation."""
        comfy_path = Path("G:/AI/Lyra/BigModes/ComfyUI_GGUF_windows_portable/ComfyUI")
        return comfy_path.exists()
    
    def _check_cube_available(self) -> bool:
        """Check if the Cube 3D generator is available."""
        cube_path = Path("G:/AI/Lyra/BigModes/cube")
        return cube_path.exists()
    
    def _get_image_generator(self):
        """Lazy-load the image generator."""
        if not self._capabilities["image"]["instance"] and self._capabilities["image"]["available"]:
            try:
                from modules.flux_integration import FluxImageGenerator
                self._capabilities["image"]["instance"] = FluxImageGenerator()
                logger.info("FLUX image generator initialized on first use")
            except Exception as e:
                logger.error(f"Error initializing FLUX image generator: {e}")
                self._capabilities["image"]["available"] = False
        return self._capabilities["image"]["instance"]
    
    def _get_vision_processor(self):
        """Lazy-load the vision processor."""
        if not self._capabilities["vision"]["instance"] and self._capabilities["vision"]["available"]:
            try:
                from modules.phi4_integration import Phi4MultimodalIntegration
                processor = Phi4MultimodalIntegration()
                if processor.is_available:
                    self._capabilities["vision"]["instance"] = processor
                    logger.info("Phi-4 vision processor initialized on first use")
                else:
                    logger.warning("Phi-4 vision processor not available after initialization")
                    self._capabilities["vision"]["available"] = False
            except Exception as e:
                logger.error(f"Error initializing Phi-4 vision processor: {e}")
                self._capabilities["vision"]["available"] = False
        return self._capabilities["vision"]["instance"]
    
    def _get_speech_processor(self):
        """Lazy-load the speech processor."""
        if not self._capabilities["speech"]["instance"] and self._capabilities["speech"]["available"]:
            # We'll use the same Phi-4 for both vision and speech
            if self._capabilities["vision"]["instance"]:
                self._capabilities["speech"]["instance"] = self._capabilities["vision"]["instance"]
            else:
                try:
                    from modules.phi4_integration import Phi4MultimodalIntegration
                    processor = Phi4MultimodalIntegration()
                    if processor.is_available:
                        self._capabilities["speech"]["instance"] = processor
                        logger.info("Phi-4 speech processor initialized on first use")
                    else:
                        logger.warning("Phi-4 speech processor not available after initialization")
                        self._capabilities["speech"]["available"] = False
                except Exception as e:
                    logger.error(f"Error initializing Phi-4 speech processor: {e}")
                    self._capabilities["speech"]["available"] = False
        return self._capabilities["speech"]["instance"]
    
    def _get_3d_generator(self):
        """Lazy-load the 3D generator."""
        if not self._capabilities["3d"]["instance"] and self._capabilities["3d"]["available"]:
            try:
                from modules.cube_integration import Cube3DGenerator
                self._capabilities["3d"]["instance"] = Cube3DGenerator()
                logger.info("Cube 3D generator initialized on first use")
            except Exception as e:
                logger.error(f"Error initializing Cube 3D generator: {e}")
                self._capabilities["3d"]["available"] = False
        return self._capabilities["3d"]["instance"]
    
    def _get_video_generator(self):
        """Lazy-load the video generator."""
        if not self._capabilities["video"]["instance"] and self._capabilities["video"]["available"]:
            try:
                # Import ComfyUI integration module
                # This is just a placeholder - implement based on your actual ComfyUI integration
                logger.info("Video generator initialization would happen here")
                self._capabilities["video"]["instance"] = True  # Replace with actual initialization
            except Exception as e:
                logger.error(f"Error initializing video generator: {e}")
                self._capabilities["video"]["available"] = False
        return self._capabilities["video"]["instance"]
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                     width: int = 1024, height: int = 1024, **kwargs) -> str:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description of the image to generate
            negative_prompt: Things to avoid in the image
            width: Image width
            height: Image height
            **kwargs: Additional parameters for the generator
            
        Returns:
            Path to the generated image or error message
        """
        if not self._capabilities["image"]["available"]:
            return "Image generation not available or disabled"
        
        generator = self._get_image_generator()
        if not generator:
            return "Failed to initialize image generator"
            
        try:
            result = generator.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                **kwargs
            )
            
            # FIXED: Improved result handling to avoid type warnings
            if isinstance(result, dict):
                if result.get("success", False) and "path" in result:
                    # Return just the file path string which Gradio can handle
                    path = result["path"]
                    # Verify the path exists to avoid further errors
                    if os.path.exists(path):
                        return path
                    else:
                        logger.warning(f"Generated image path does not exist: {path}")
                        return f"Error: Generated image path not found: {path}"
                elif not result.get("success", False):
                    # Return the error message
                    return f"Error: {result.get('error', 'Unknown error')}"
            elif isinstance(result, str):
                # If path was returned directly as string
                if os.path.exists(result) and any(result.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                    return result
                else:
                    # It might be an error message or invalid path
                    return f"Result: {result}"
            else:
                # For any other type of result
                return "Generated image could not be processed: unexpected result type"
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return f"Error generating image: {str(e)}"
    
    def process_image(self, image_path: Union[str, Path], prompt: str = "") -> Dict[str, Any]:
        """
        Process an image using vision capabilities.
        
        Args:
            image_path: Path to the image to process
            prompt: Optional prompt to guide processing
            
        Returns:
            Dictionary with processing results
        """
        if not self._capabilities["vision"]["available"]:
            return {
                "success": False, 
                "error": "Vision processing not available or disabled"
            }
        
        processor = self._get_vision_processor()
        if not processor:
            return {
                "success": False, 
                "error": "Failed to initialize vision processor"
            }
            
        try:
            result = processor.process_image(image_path, prompt)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "success": False,
                "error": f"Error processing image: {str(e)}"
            }
    
    def generate_3d_model(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a 3D model from a text prompt.
        
        Args:
            prompt: Text description of the 3D model to generate
            **kwargs: Additional parameters for the generator
            
        Returns:
            Dictionary with generation results
        """
        if not self._capabilities["3d"]["available"]:
            return {
                "success": False, 
                "error": "3D generation not available or disabled"
            }
        
        generator = self._get_3d_generator()
        if not generator:
            return {
                "success": False, 
                "error": "Failed to initialize 3D generator"
            }
            
        try:
            return generator.generate_3d_model(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Error generating 3D model: {e}")
            return {
                "success": False,
                "error": f"Error generating 3D model: {str(e)}"
            }
    
    def transcribe_speech(self, audio_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Transcribe speech from an audio file.
        
        Args:
            audio_path: Path to the audio file to transcribe
            
        Returns:
            Dictionary with transcription results
        """
        if not self._capabilities["speech"]["available"]:
            return {
                "success": False, 
                "error": "Speech processing not available or disabled"
            }
        
        processor = self._get_speech_processor()
        if not processor:
            return {
                "success": False, 
                "error": "Failed to initialize speech processor"
            }
            
        try:
            result = processor.transcribe_speech(audio_path)
            return {
                "success": True,
                "transcript": result
            }
        except Exception as e:
            logger.error(f"Error transcribing speech: {e}")
            return {
                "success": False,
                "error": f"Error transcribing speech: {str(e)}"
            }
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get a dictionary of available capabilities."""
        return {k: v["available"] for k, v in self._capabilities.items()}
    
    def get_capability_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about available capabilities."""
        return [
            {
                "name": v["name"],
                "type": k,
                "available": v["available"],
                "enabled": self.options.get(f"enable_{k}", True)
            }
            for k, v in self._capabilities.items()
        ]
