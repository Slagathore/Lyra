"""
Image generation module for Lyra with NSFW support
"""

import os
import time
import logging
import uuid
import requests
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, List, Any, Union, Tuple
from datetime import datetime
from PIL import Image
import base64

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check diffusers availability (local generation)
try:
    import torch
    from diffusers import StableDiffusionPipeline, DiffusionPipeline
    from diffusers.schedulers import DDIMScheduler, DPMSolverMultistepScheduler
    DIFFUSERS_AVAILABLE = True
    logger.info("Diffusers available for local image generation")
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("Diffusers not available, will attempt to use API services")

# Default directories
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "output", "images")
DEFAULT_MODEL_DIR = os.environ.get("LYRA_MODEL_DIR", os.path.join(os.path.expanduser("~"), "lyra_models"))
DEFAULT_MODEL_ID = "runwayml/stable-diffusion-v1-5"  # SFW default
NSFW_MODEL_ID = "dreamlike-art/dreamlike-diffusion-1.0"  # More permissive model

# Ensure output directory exists
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

class ImageGenerator:
    """
    Image generation class for Lyra with multiple backends and NSFW support
    """
    
    def __init__(self, 
                 model_id_or_path: str = DEFAULT_MODEL_ID,
                 output_dir: str = DEFAULT_OUTPUT_DIR,
                 nsfw_allowed: bool = True,
                 use_gpu: bool = True):
        """
        Initialize image generator
        
        Args:
            model_id_or_path: Model ID or path to use for generation
            output_dir: Directory to save generated images
            nsfw_allowed: Whether to allow NSFW content
            use_gpu: Whether to use GPU acceleration if available
        """
        self.output_dir = output_dir
        self.nsfw_allowed = nsfw_allowed
        self.model_id = model_id_or_path
        self.model_path = self._resolve_model_path(model_id_or_path)
        self.use_gpu = use_gpu and torch.cuda.is_available() if DIFFUSERS_AVAILABLE else False
        self.pipe = None
        self.nsfw_pipe = None
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize API keys from environment
        self.stability_api_key = os.environ.get("STABILITY_API_KEY")
        self.dream_studio_api_key = os.environ.get("DREAM_STUDIO_API_KEY")
        
        logger.info(f"Image generator initialized with model: {self.model_id}")
        logger.info(f"NSFW content: {'Allowed' if self.nsfw_allowed else 'Disallowed'}")
        logger.info(f"Output directory: {self.output_dir}")
        
    def _resolve_model_path(self, model_id_or_path: str) -> str:
        """Resolve model ID to local path if cached"""
        if os.path.exists(model_id_or_path):
            return model_id_or_path
            
        # Check if it exists in the model directory
        model_dir_path = os.path.join(DEFAULT_MODEL_DIR, model_id_or_path.replace("/", "_"))
        if os.path.exists(model_dir_path):
            return model_dir_path
            
        # Otherwise, assume it's a Hugging Face model ID
        return model_id_or_path
        
    def _load_model(self, nsfw_model: bool = False) -> bool:
        """
        Load the diffusion model
        
        Args:
            nsfw_model: Whether to load the NSFW model
            
        Returns:
            True if model loaded successfully
        """
        if not DIFFUSERS_AVAILABLE:
            logger.error("Cannot load model: Diffusers not available")
            return False
            
        try:
            model_id = NSFW_MODEL_ID if nsfw_model else self.model_id
            
            # Determine the appropriate pipeline type based on model
            pipeline_cls = StableDiffusionPipeline
            
            logger.info(f"Loading {'NSFW' if nsfw_model else 'standard'} model: {model_id}")
            
            # Set up the device configuration
            device = "cuda" if self.use_gpu else "cpu"
            torch_dtype = torch.float16 if self.use_gpu else torch.float32
            
            # Load the pipeline with memory optimizations
            pipe = pipeline_cls.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                safety_checker=None if self.nsfw_allowed else pipe.safety_checker,
                feature_extractor=None if self.nsfw_allowed else pipe.feature_extractor
            )
            
            # Replace scheduler for better quality
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                pipe.scheduler.config,
                algorithm_type="dpmsolver++",
                solver_order=2
            )
            
            # Move to device and optimize
            pipe = pipe.to(device)
            
            # Enable memory optimizations if on GPU
            if self.use_gpu:
                pipe.enable_attention_slicing()
                pipe.enable_vae_tiling()
                if hasattr(pipe, 'enable_xformers_memory_efficient_attention'):
                    pipe.enable_xformers_memory_efficient_attention()
            
            # Store the pipeline
            if nsfw_model:
                self.nsfw_pipe = pipe
            else:
                self.pipe = pipe
                
            logger.info(f"Successfully loaded {'NSFW' if nsfw_model else 'standard'} model")
            return True
            
        except Exception as e:
            logger.error(f"Error loading diffusion model: {e}")
            return False
            
    def _check_nsfw_prompt(self, prompt: str) -> bool:
        """
        Check if a prompt is likely NSFW
        
        Args:
            prompt: Text prompt to check
            
        Returns:
            True if prompt appears to be NSFW
        """
        # Simple keyword-based check
        nsfw_keywords = [
            "nude", "naked", "sex", "porn", "xxx", "adult", "nsfw", 
            "explicit", "18+", "erotic", "sexual", "vagina", "penis", 
            "breasts", "nipples", "genitals"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in nsfw_keywords)
    
    def generate_image(self, 
                       prompt: str,
                       negative_prompt: str = "blurry, low quality, low resolution, watermarks, signatures",
                       width: int = 512,
                       height: int = 512,
                       num_inference_steps: int = 30,
                       guidance_scale: float = 7.5,
                       force_nsfw: bool = False) -> Optional[str]:
        """
        Generate an image from a prompt
        
        Args:
            prompt: Text description to generate image from
            negative_prompt: Elements to avoid in the image
            width: Image width in pixels
            height: Image height in pixels
            num_inference_steps: Number of denoising steps
            guidance_scale: How closely to follow the prompt
            force_nsfw: Force NSFW model even if prompt doesn't appear NSFW
        
        Returns:
            Path to the generated image or None if generation failed
        """
        # Check if prompt is NSFW
        is_nsfw_prompt = force_nsfw or self._check_nsfw_prompt(prompt)
        
        # If NSFW content is not allowed, modify the prompt
        if is_nsfw_prompt and not self.nsfw_allowed:
            logger.warning("NSFW prompt detected but NSFW content is not allowed. Modifying prompt.")
            negative_prompt += ", nsfw, nudity, naked, sexual content, adult content"
            
        # Try diffusers first if available
        if DIFFUSERS_AVAILABLE:
            # Load the appropriate model if not already loaded
            if is_nsfw_prompt and self.nsfw_allowed:
                if self.nsfw_pipe is None and not self._load_model(nsfw_model=True):
                    logger.warning("Failed to load NSFW model, falling back to standard model")
                    is_nsfw_prompt = False
                    
            if not is_nsfw_prompt and self.pipe is None and not self._load_model(nsfw_model=False):
                logger.error("Failed to load standard model")
                return self._fallback_generate(prompt, width, height)
                
            # Generate the image
            try:
                pipe = self.nsfw_pipe if is_nsfw_prompt and self.nsfw_allowed else self.pipe
                
                logger.info(f"Generating image with prompt: {prompt}")
                result = pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                )
                
                # Save the image
                image = result.images[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lyra_image_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(self.output_dir, filename)
                
                image.save(output_path)
                logger.info(f"Image generated successfully: {output_path}")
                
                return output_path
                
            except Exception as e:
                logger.error(f"Error generating image with diffusers: {e}")
                return self._fallback_generate(prompt, width, height)
        
        # If diffusers not available or failed, use fallback method
        return self._fallback_generate(prompt, width, height)
    
    def _fallback_generate(self, prompt: str, width: int = 512, height: int = 512) -> Optional[str]:
        """
        Fallback to API services for image generation
        
        Args:
            prompt: Text prompt
            width: Image width
            height: Image height
            
        Returns:
            Path to generated image or None
        """
        logger.info("Using fallback API for image generation")
        
        # Try Stability AI API first if key is available
        if self.stability_api_key:
            try:
                return self._generate_stability_api(prompt, width, height)
            except Exception as e:
                logger.error(f"Stability API generation failed: {e}")
        
        # Try Dream Studio API next
        if self.dream_studio_api_key:
            try:
                return self._generate_dreamstudio_api(prompt, width, height)
            except Exception as e:
                logger.error(f"Dream Studio API generation failed: {e}")
                
        logger.error("All image generation methods failed")
        return None
    
    def _generate_stability_api(self, prompt: str, width: int, height: int) -> Optional[str]:
        """Generate image using Stability AI API"""
        url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-5/text-to-image"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.stability_api_key}"
        }
        
        body = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            for i, image in enumerate(data["artifacts"]):
                img_data = base64.b64decode(image["base64"])
                
                # Save the image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lyra_stability_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(self.output_dir, filename)
                
                with open(output_path, "wb") as f:
                    f.write(img_data)
                
                return output_path
                
        logger.error(f"Stability API error: {response.status_code}, {response.text}")
        return None
    
    def _generate_dreamstudio_api(self, prompt: str, width: int, height: int) -> Optional[str]:
        """Generate image using Dream Studio API (another Stability AI endpoint)"""
        engine_id = "stable-diffusion-v1-5"
        url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.dream_studio_api_key}"
        }
        
        body = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            for i, image in enumerate(data["artifacts"]):
                img_data = base64.b64decode(image["base64"])
                
                # Save the image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lyra_dreamstudio_{timestamp}_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(self.output_dir, filename)
                
                with open(output_path, "wb") as f:
                    f.write(img_data)
                
                return output_path
                
        logger.error(f"Dream Studio API error: {response.status_code}, {response.text}")
        return None

# Create a singleton for easy access
_image_generator = None

def get_image_generator(**kwargs) -> ImageGenerator:
    """Get or create the image generator singleton"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator(**kwargs)
    return _image_generator

def generate_image(prompt: str, **kwargs) -> Optional[str]:
    """
    Generate an image from a prompt
    
    Args:
        prompt: Text prompt for the image
        **kwargs: Additional arguments for the generator
        
    Returns:
        Path to the generated image or None if generation failed
    """
    generator = get_image_generator()
    return generator.generate_image(prompt, **kwargs)

if __name__ == "__main__":
    # Test image generation
    output_path = generate_image(
        "A beautiful sunset over a calm ocean, photorealistic, 8k, detailed",
        width=768,
        height=512
    )
    
    if output_path:
        print(f"Image generated successfully: {output_path}")
        # Try to display the image if PIL is available
        try:
            img = Image.open(output_path)
            img.show()
        except:
            pass
    else:
        print("Image generation failed")
