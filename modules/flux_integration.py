import logging
import os
import json
import torch
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import time
import random
import uuid
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

class FluxImageGenerator:
    """
    Integration with FLUX.1 image generation model.
    """
    
    def __init__(self):
        self.flux_path = Path("G:/AI/Full Models/FLUX.1-dev")
        self.is_available = self._check_availability()
        self.model = None
        self.pipeline = None
        self.model_index = None
        self.nsfw_model_path = self.flux_path / "Flux-Unred.safetensors"
        
        if self.is_available:
            logger.info("FLUX.1 model found, initializing integration")
            self._load_model_index()
            # Don't initialize the model immediately to save memory
            # It will be loaded on first use
        else:
            logger.warning("FLUX.1 model not found or incomplete")
    
    def _check_availability(self) -> bool:
        """Check if the FLUX model is available."""
        if not self.flux_path.exists():
            return False
            
        # Check if model index exists
        model_index_exists = (self.flux_path / "model_index.json").exists()
        
        return model_index_exists
    
    def _load_model_index(self):
        """Load the model index file."""
        try:
            model_index_path = self.flux_path / "model_index.json"
            if model_index_path.exists():
                with open(model_index_path, 'r') as f:
                    self.model_index = json.load(f)
                logger.info(f"Loaded FLUX model index with {len(self.model_index)} entries")
            else:
                logger.error("FLUX model index not found")
        except Exception as e:
            logger.error(f"Error loading FLUX model index: {e}")
    
    def _initialize(self, nsfw=False):
        """Initialize the FLUX model."""
        if self.pipeline is not None:
            return True
            
        try:
            # Import diffusers
            from diffusers import FluxPipeline, FluxScheduler
            
            # Determine which model file to use
            if nsfw and self.nsfw_model_path.exists():
                model_path = self.nsfw_model_path
                logger.info("Using NSFW model: Flux-Unred.safetensors")
            else:
                # Use default model (first one in index)
                if self.model_index and len(self.model_index) > 0:
                    default_model = self.model_index[0]
                    model_path = self.flux_path / default_model["file"]
                else:
                    logger.error("No default model found in index")
                    return False
            
            # Check if model file exists
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
                
            # Initialize the pipeline
            logger.info(f"Loading FLUX pipeline with model: {model_path}")
            self.pipeline = FluxPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info("FLUX pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing FLUX model: {e}")
            return False
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                      width: int = 1024, height: int = 1024,
                      steps: int = 30, guidance_scale: float = 7.5,
                      nsfw_allowed: bool = False, seed: int = None) -> Dict[str, Any]:
        """
        Generate an image using FLUX.
        
        Args:
            prompt: Text prompt for image generation
            negative_prompt: Things to avoid in the image
            width: Image width (default: 1024)
            height: Image height (default: 1024)
            steps: Number of diffusion steps (default: 30)
            guidance_scale: How closely to follow the prompt (default: 7.5)
            nsfw_allowed: Whether NSFW content is allowed (default: False)
            seed: Random seed for reproducibility (default: random)
            
        Returns:
            Dict with generation results
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "FLUX model is not available"
            }
        
        # Check for NSFW keywords in prompt
        nsfw_content_detected = self._check_nsfw_prompt(prompt)
        
        # If NSFW content is detected but not allowed, return error
        if nsfw_content_detected and not nsfw_allowed:
            return {
                "success": False,
                "error": "NSFW content detected in prompt but not allowed",
                "nsfw_detected": True
            }
        
        # Initialize the model if needed (with NSFW model if appropriate)
        if not self._initialize(nsfw=nsfw_allowed and nsfw_content_detected):
            return {
                "success": False,
                "error": "Failed to initialize FLUX model"
            }
        
        try:
            # Use provided seed or generate random one
            if seed is None:
                seed = random.randint(0, 2147483647)
            
            # Set the seed for reproducibility
            torch.manual_seed(seed)
            
            # Create output directory
            output_dir = Path("generated/images")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate a unique filename
            timestamp = int(time.time())
            uid = str(uuid.uuid4())[:8]
            output_filename = f"flux_{timestamp}_{uid}.png"
            output_path = output_dir / output_filename
            
            # Log generation parameters
            logger.info(f"Generating image with prompt: {prompt}")
            logger.info(f"Parameters: {width}x{height}, steps={steps}, guidance={guidance_scale}, seed={seed}")
            
            # Generate the image
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance_scale
            ).images[0]
            
            # Save the image
            image.save(output_path)
            
            # Create metadata file
            metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "guidance_scale": guidance_scale,
                "seed": seed,
                "model": "FLUX.1",
                "nsfw_allowed": nsfw_allowed,
                "nsfw_detected": nsfw_content_detected,
                "timestamp": timestamp
            }
            
            metadata_path = output_path.with_suffix(".json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Image generated successfully: {output_path}")
            
            return {
                "success": True,
                "path": str(output_path),
                "seed": seed,
                "nsfw_detected": nsfw_content_detected,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_nsfw_prompt(self, prompt: str) -> bool:
        """
        Check if the prompt contains NSFW keywords.
        
        Args:
            prompt: The text prompt to check
            
        Returns:
            True if NSFW content is detected, False otherwise
        """
        # Simple list of NSFW keywords to check
        nsfw_keywords = [
            "nude", "naked", "nsfw", "porn", "sex", "explicit", "adult", "xxx",
            "erotic", "18+", "mature", "uncensored", "unfiltered", "unrestricted"
        ]
        
        prompt_lower = prompt.lower()
        for keyword in nsfw_keywords:
            if keyword in prompt_lower:
                logger.info(f"NSFW keyword detected in prompt: {keyword}")
                return True
        
        return False
    
    def change_model(self, model_name: str) -> bool:
        """
        Change the active FLUX model.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            True if model was changed successfully, False otherwise
        """
        if not self.is_available or not self.model_index:
            return False
        
        # Find the model in the index
        selected_model = None
        for model in self.model_index:
            if model["name"] == model_name:
                selected_model = model
                break
        
        if selected_model is None:
            logger.error(f"Model not found in index: {model_name}")
            return False
        
        try:
            # Clear existing pipeline to free memory
            if self.pipeline is not None:
                del self.pipeline
                import gc
                gc.collect()
                torch.cuda.empty_cache()
                self.pipeline = None
            
            # Import required modules
            from diffusers import FluxPipeline
            
            model_path = self.flux_path / selected_model["file"]
            
            # Check if model file exists
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Initialize new pipeline
            logger.info(f"Loading FLUX pipeline with model: {model_path}")
            self.pipeline = FluxPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            logger.info(f"Changed FLUX model to: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing FLUX model: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available FLUX models."""
        if not self.model_index:
            return []
        
        # Return a simplified list with just name and description
        return [
            {"name": model["name"], "description": model.get("description", "")}
            for model in self.model_index
        ]

class FluxInterface:
    """Interface for the FLUX model."""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        
    def load_model(self):
        """Load the FLUX model."""
        if self.model is None:
            try:
                # Model loading implementation
                print("Loading FLUX model from:", self.model_path)
                # Implement actual model loading logic here
                self.model = True  # Placeholder for actual model
            except Exception as e:
                print(f"Error loading FLUX model: {e}")
                return False
        return True
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                      width: int = 512, height: int = 512, 
                      num_inference_steps: int = 50, guidance_scale: float = 7.5):
        """Generate an image using the FLUX model."""
        if not self.load_model():
            return None
        
        try:
            # Actual image generation would happen here
            print(f"Generating image with prompt: {prompt}")
            # Mock image generation result
            image = Image.new('RGB', (width, height), color='gray')
            return image
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def get_model_info(self):
        """Get information about the loaded model."""
        if self.model:
            return {
                "name": "FLUX",
                "version": "1.0",
                "capabilities": ["text-to-image"]
            }
        return None
