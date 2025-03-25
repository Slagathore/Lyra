import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_model_config():
    try:
        config_dir = os.path.join('config', 'model_configs')
        os.makedirs(config_dir, exist_ok=True)
        
        phi_config_path = os.path.join(config_dir, 'phi-4.json')
        if not os.path.exists(phi_config_path):
            config = {
                'model_name': 'phi-4',
                'model_path': r'G:\AI\Lyra\BigModes\Phi-4-multimodal-instruct-abliterated',
                'model_type': 'phi',
                'parameters': {
                    'format': 'multimodal',
                    'vision_enabled': True,
                    'audio_enabled': True,
                    'speech_enabled': True,
                    'context_size': 131072,
                    'use_transformers': True,
                    'trust_remote_code': True,
                    'attn_implementation': 'flash_attention_2',
                    'torch_dtype': 'bfloat16',
                    'n_gpu_layers': -1
                }
            }
            with open(phi_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Created Phi-4 model configuration")
        else:
            logger.info("Phi-4 model configuration already exists")
        return True
    except Exception as e:
        logger.error(f"Error setting up model config: {str(e)}")
        return False

def ensure_cognitive_config():
    try:
        cognitive_config_path = os.path.join('config', 'cognitive_config.json')
        if not os.path.exists(cognitive_config_path):
            config = {
                "metacognition_enabled": True,
                "emotional_core_enabled": True,
                "deep_memory_enabled": True,
                "extended_thinking_enabled": True,
                "boredom_enabled": True,
                "multimodal_enabled": True,
                "audio_processing_enabled": True
            }
            with open(cognitive_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Created cognitive module configuration")
        else:
            logger.info("Cognitive configuration already exists")
        return True
    except Exception as e:
        logger.error(f"Error setting up cognitive config: {str(e)}")
        return False

if __name__ == "__main__":
    model_success = ensure_model_config()
    cognitive_success = ensure_cognitive_config()
    exit(0 if model_success and cognitive_success else 1)