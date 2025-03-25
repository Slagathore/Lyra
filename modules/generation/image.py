# ...existing code...

def generate_image(prompt, model_name="stable-diffusion", width=512, height=512, steps=20, seed=-1):
    try:
        logger.info(f"Generating image from prompt: {prompt} using {model_name}")
        
        # Check if diffusers is installed
        try:
            from diffusers import StableDiffusionPipeline
            import torch
        except ImportError:
            logger.error("Diffusers library not installed. Please install it with: pip install diffusers transformers")
            return None, "Error: Required libraries not installed"
            
        # Set default model if needed
        if not model_name or model_name == "stable-diffusion":
            model_name = "runwayml/stable-diffusion-v1-5"
            
        # Initialize the pipeline
        try:
            pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
            
            # Use CUDA if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            pipe = pipe.to(device)
            
            # Enable attention slicing for lower memory usage
            pipe.enable_attention_slicing()
            
            # Set random seed if provided
            generator = None
            if seed >= 0:
                generator = torch.Generator(device=device).manual_seed(seed)
            
            # Generate the image
            image = pipe(prompt, width=width, height=height, num_inference_steps=steps, generator=generator).images[0]
            
            # Save the image to a temporary file
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            import time
            timestamp = int(time.time())
            image_path = os.path.join(temp_dir, f"lyra_image_{timestamp}.png")
            image.save(image_path)
            
            logger.info(f"Image generated successfully and saved to {image_path}")
            return image_path, None
            
        except Exception as e:
            error_msg = f"Error during image generation: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
            
    except Exception as e:
        error_msg = f"Error in generate_image: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

# ...existing code...
