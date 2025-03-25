"""
Phi-4 Multimodal Integration for Lyra
Handles loading and using Microsoft's Phi-4 multimodal model
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Set up logging
logger = logging.getLogger(__name__)

class Phi4MultimodalIntegration:
    """
    Integration for Phi-4 Multimodal model
    Handles loading and interacting with the model
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the Phi-4 multimodal integration
        
        Args:
            model_path: Path to the model, defaults to huggingface model
        """
        self.model = None
        self.processor = None
        self.generation_config = None
        self.is_available = self._check_availability()
        self.phi4_path = model_path or "huihui-ai/Phi-4-multimodal-instruct-abliterated"
        
        # Integration settings
        self._settings = {
            "torch_dtype": "bfloat16",
            "trust_remote_code": True,
            "attn_implementation": "flash_attention_2",
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "repetition_penalty": 1.1
        }
        
        # Prompt settings
        self.user_prompt = '<|user|>'
        self.assistant_prompt = '<|assistant|>'
        self.prompt_suffix = '<|end|>'
    
    def _check_availability(self) -> bool:
        """
        Check if the necessary libraries are available
        
        Returns:
            True if all required libraries are available
        """
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
            return True
        except ImportError as e:
            logger.warning(f"Missing required libraries for Phi-4 multimodal: {e}")
            return False
    
    def _check_gpu_compatibility(self) -> bool:
        """
        Check if the GPU is compatible with the model
        
        Returns:
            True if compatible GPU is available
        """
        try:
            import torch
            
            if not torch.cuda.is_available():
                logger.warning("CUDA not available for Phi-4 multimodal")
                return False
                
            # Check CUDA version
            cuda_version = torch.version.cuda
            if cuda_version is None:
                logger.warning("Could not determine CUDA version")
                return False
                
            # Phi-4 requires CUDA 11.8+
            cuda_version_float = float(".".join(cuda_version.split(".")[:2]))
            if cuda_version_float < 11.8:
                logger.warning(f"CUDA version {cuda_version} is below required version 11.8 for Phi-4 multimodal")
                return False
                
            logger.info(f"Compatible CUDA version {cuda_version} detected")
            return True
        except Exception as e:
            logger.error(f"Error checking GPU compatibility: {e}")
            return False
    
    def load_model(self, **kwargs):
        """
        Load the Phi-4 multimodal model
        
        Args:
            **kwargs: Additional arguments for model loading
            
        Returns:
            The loaded model or None if loading failed
        """
        if not self.is_available:
            logger.error("Required libraries not available for Phi-4 multimodal")
            return None
        
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
            
            # Update settings with kwargs
            for key, value in kwargs.items():
                if key in self._settings:
                    self._settings[key] = value
            
            # Check if the model path exists locally or on huggingface
            model_path = self.phi4_path
            
            # Load processor
            logger.info(f"Loading processor from {model_path}")
            self.processor = AutoProcessor.from_pretrained(
                model_path,
                trust_remote_code=self._settings["trust_remote_code"]
            )
            
            # Load model
            logger.info(f"Loading Phi-4 multimodal model from {model_path}")
            
            # Determine torch dtype
            torch_dtype = self._settings["torch_dtype"]
            if torch_dtype == "auto":
                torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
            elif torch_dtype == "bfloat16":
                torch_dtype = torch.bfloat16
            elif torch_dtype == "float16":
                torch_dtype = torch.float16
            elif torch_dtype == "float32":
                torch_dtype = torch.float32
                
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=self._settings["trust_remote_code"],
                torch_dtype=torch_dtype,
                _attn_implementation=self._settings["attn_implementation"],
            )
            
            # Move model to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("Moved model to CUDA")
            
            # Load generation config
            try:
                self.generation_config = GenerationConfig.from_pretrained(model_path, 'generation_config.json')
                logger.info("Loaded generation config")
            except Exception as e:
                logger.warning(f"Could not load generation config: {e}")
                self.generation_config = None
            
            logger.info("Phi-4 multimodal model loaded successfully")
            return self.model
            
        except Exception as e:
            logger.error(f"Error loading Phi-4 multimodal model: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def process_image(self, image_path):
        """
        Process an image for use with the model
        
        Args:
            image_path: Path to the image
            
        Returns:
            Processed image
        """
        if not self.processor:
            logger.error("Processor not initialized")
            return None
            
        try:
            from PIL import Image
            
            # Load image
            if isinstance(image_path, str):
                if os.path.exists(image_path):
                    image = Image.open(image_path)
                else:
                    logger.error(f"Image not found: {image_path}")
                    return None
            elif hasattr(image_path, 'read'):  # File-like object
                image = Image.open(image_path)
            else:
                # Assume it's already a PIL Image
                image = image_path
                
            # Return the image directly - the processor will handle it during generation
            return image
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def process_audio(self, audio_path):
        """
        Process audio for use with the model
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Processed audio
        """
        if not self.processor:
            logger.error("Processor not initialized")
            return None
            
        try:
            import soundfile as sf
            import numpy as np
            
            # Load audio
            if isinstance(audio_path, str):
                if os.path.exists(audio_path):
                    audio_data, sample_rate = sf.read(audio_path)
                    return {"audio_data": audio_data, "sample_rate": sample_rate}
                else:
                    logger.error(f"Audio file not found: {audio_path}")
                    return None
            elif hasattr(audio_path, 'read'):  # File-like object
                audio_data, sample_rate = sf.read(audio_path)
                return {"audio_data": audio_data, "sample_rate": sample_rate}
            else:
                # Assume it's already in the right format
                return audio_path
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    
    def generate(self, prompt: str, images=None, audio=None, **kwargs):
        """
        Generate a response using the Phi-4 multimodal model
        
        Args:
            prompt: The text prompt
            images: Optional image input(s)
            audio: Optional audio input(s)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.model or not self.processor:
            logger.error("Model or processor not initialized")
            return "Error: Model not initialized. Please load the model first."
            
        try:
            # Format prompt
            formatted_prompt = f'{self.user_prompt}{prompt}{self.prompt_suffix}{self.assistant_prompt}'
            
            # Process images if provided
            if images is not None:
                if not isinstance(images, list):
                    images = [images]
                
                # Process each image
                processed_images = []
                for img in images:
                    processed = self.process_image(img)
                    if processed:
                        processed_images.append(processed)
                
                if not processed_images:
                    images = None
                else:
                    images = processed_images
                    
            # Process audio if provided
            if audio is not None:
                audio = self.process_audio(audio)
                
            # Prepare inputs
            inputs = self.processor(
                formatted_prompt, 
                images=images, 
                return_tensors='pt'
            )
            
            # Move inputs to GPU if available
            import torch
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda:0") if hasattr(v, 'to') else v for k, v in inputs.items()}
            
            # Get generation parameters
            generation_params = {
                'max_new_tokens': kwargs.get('max_tokens', self._settings['max_tokens']),
                'do_sample': kwargs.get('do_sample', True),
                'temperature': kwargs.get('temperature', self._settings['temperature']),
                'top_p': kwargs.get('top_p', self._settings['top_p']),
                'top_k': kwargs.get('top_k', self._settings['top_k']),
                'repetition_penalty': kwargs.get('repetition_penalty', self._settings['repetition_penalty']),
            }
            
            # Generate response
            if self.generation_config:
                generation_ids = self.model.generate(
                    **inputs,
                    generation_config=self.generation_config,
                    **generation_params
                )
            else:
                generation_ids = self.model.generate(
                    **inputs,
                    **generation_params
                )
            
            # Extract only the newly generated tokens
            generation_ids = generation_ids[:, inputs['input_ids'].shape[1]:]
            
            # Decode response
            response = self.processor.batch_decode(
                generation_ids, 
                skip_special_tokens=True, 
                clean_up_tokenization_spaces=False
            )[0]
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating response: {str(e)}"
    
    def unload(self):
        """
        Unload the model to free up memory
        
        Returns:
            True if successful
        """
        try:
            import torch
            
            # Delete model and processor
            if self.model:
                del self.model
                self.model = None
            
            if self.processor:
                del self.processor
                self.processor = None
            
            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info("Phi-4 multimodal model unloaded")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return False
