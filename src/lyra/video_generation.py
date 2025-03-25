"""
Video Generation Integration for Lyra using Wan2.1-I2V-14B-480P
"""

import os
import torch
import logging
from pathlib import Path
from PIL import Image
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if we have diffusers installed
try:
    from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
    from diffusers.utils import export_to_video
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.error("Diffusers library not available. Video generation will not work.")

# Configuration
MODEL_DIR = os.environ.get("LYRA_MODEL_DIR", os.path.join(os.path.expanduser("~"), "lyra_models"))
VIDEO_MODEL_ID = os.environ.get("LYRA_VIDEO_MODEL", "Wan-AI/Wan2.1-I2V-14B-480P")
VIDEO_MODEL_PATH = os.path.join(MODEL_DIR, VIDEO_MODEL_ID.replace("/", "_"))
OUTPUT_DIR = os.environ.get("LYRA_OUTPUT_DIR", os.path.join(os.getcwd(), "output", "videos"))

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class VideoGenerator:
    """
    Video generation using Wan2.1-I2V-14B-480P model
    """
    def __init__(self, model_path=None):
        """
        Initialize the video generator
        
        Args:
            model_path: Path to the model (defaults to VIDEO_MODEL_PATH)
        """
        if model_path is None:
            model_path = VIDEO_MODEL_PATH
            
        self.model_path = model_path
        self.pipe = None
        
    def load_model(self):
        """Load the video generation model"""
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("Diffusers library not available. Cannot load video model.")
            
        if self.pipe is not None:
            return  # Model already loaded
            
        logger.info(f"Loading video model from {self.model_path}")
        
        try:
            # Get the device to use
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cpu":
                logger.warning("CUDA not available. Using CPU for video generation will be very slow.")
                
            # Check if model exists locally, otherwise use the model ID
            model_path = self.model_path if os.path.exists(self.model_path) else VIDEO_MODEL_ID
                
            # Load the pipeline
            self.pipe = DiffusionPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            
            # Move to device and optimize
            self.pipe.to(device)
            
            # Use more efficient scheduler
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
            
            # Enable memory optimization if on CUDA
            if device == "cuda":
                self.pipe.enable_model_cpu_offload()
                if torch.cuda.is_available():
                    self.pipe.enable_vae_slicing()
            
            logger.info("Video model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load video model: {e}")
            return False
            
    def generate_video(self, prompt: str, negative_prompt: str = None,
                      num_frames: int = 24, height: int = 480, width: int = 864,
                      num_inference_steps: int = 25) -> Optional[str]:
        """
        Generate a video from a text prompt
        
        Args:
            prompt: Text description of the video to generate
            negative_prompt: Negative prompt (what to avoid)
            num_frames: Number of frames to generate
            height: Height of the video
            width: Width of the video
            num_inference_steps: Number of denoising steps
            
        Returns:
            Path to the generated video file or None if generation failed
        """
        if not self.load_model():
            return None
            
        try:
            # Generate video frames
            logger.info(f"Generating video for prompt: {prompt}")
            
            # Set default negative prompt if not provided
            if negative_prompt is None:
                negative_prompt = "low quality, blurry, pixelated, distorted, ugly, poor lighting"
                
            # Generate frames
            frames = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_frames=num_frames,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
            ).frames
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lyra_video_{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(OUTPUT_DIR, filename)
            
            # Export frames to video file
            export_to_video(frames, output_path)
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None

# Singleton instance
_video_generator = None

def generate_video(prompt: str, **kwargs) -> Optional[str]:
    """
    Generate a video from a text prompt (singleton wrapper)
    
    Args:
        prompt: Text description of the video to generate
        **kwargs: Additional arguments for video generation
        
    Returns:
        Path to the generated video file or None if generation failed
    """
    global _video_generator
    
    if _video_generator is None:
        _video_generator = VideoGenerator()
        
    return _video_generator.generate_video(prompt, **kwargs)

if __name__ == "__main__":
    # Test video generation
    output_path = generate_video(
        "A beautiful sunset over a calm ocean with waves gently lapping at the shore",
        num_frames=24,
        num_inference_steps=25
    )
    
    if output_path:
        print(f"Video generated successfully: {output_path}")
    else:
        print("Video generation failed")
