"""
Standalone model testing module for Lyra
"""
import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path

# Set up logging
logger = logging.getLogger("model_tester")

# Constants
TEST_RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "data", "model_test_results.json")

def ensure_test_results_dir():
    """Ensure the directory for test results exists"""
    os.makedirs(os.path.dirname(TEST_RESULTS_FILE), exist_ok=True)

def load_test_results():
    """Load previous test results"""
    ensure_test_results_dir()
    if not os.path.exists(TEST_RESULTS_FILE):
        return {}
    
    try:
        with open(TEST_RESULTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading test results: {e}")
        return {}

def save_test_results(results):
    """Save test results to file"""
    ensure_test_results_dir()
    try:
        with open(TEST_RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving test results: {e}")

def get_model_test_status(model_name):
    """
    Check if a model has been tested and return its status
    
    Returns:
    - dict: Test results for the model, or None if not tested
    """
    results = load_test_results()
    return results.get(model_name)

def detect_model_type(model_path):
    """
    Attempt to detect the model type based on file inspection
    """
    try:
        # Check file extension first
        ext = os.path.splitext(model_path)[1].lower()
        
        # GGUF models
        if ext == '.gguf':
            return 'gguf'
        
        # GGML models
        if ext == '.ggml' or ext == '.bin':
            return 'ggml'
        
        # Check for PyTorch models
        if ext == '.pt' or ext == '.pth':
            return 'pytorch'
        
        # For other files, check the magic bytes/header
        with open(model_path, 'rb') as f:
            header = f.read(16)  # Read first 16 bytes
            
            # GGUF models start with "GGUF" (0x47475546) in their header
            if header[:4] == b'GGUF':
                return 'gguf'
            
            # GGML v3 models start with 0x67676d6c (ggml in ASCII)
            if header[:4] == b'ggml':
                return 'ggml'
            
            # Try to detect HuggingFace format
            # Check for model.safetensors, config.json, or pytorch_model.bin in same dir
            model_dir = os.path.dirname(model_path)
            if os.path.exists(os.path.join(model_dir, 'config.json')):
                return 'transformers'
            
            if os.path.exists(os.path.join(model_dir, 'model.safetensors')) or \
               os.path.exists(os.path.join(model_dir, 'pytorch_model.bin')):
                return 'transformers'
        
        # If we can't determine, return Unknown
        return 'Unknown'
    
    except Exception as e:
        logger.error(f"Error detecting model type: {e}")
        return 'Unknown'

def validate_model_with_initializer(model_path, init_type):
    """
    Validate a model with a specific initializer
    Returns True if validation was successful
    """
    # This is a simplified validation that doesn't actually load models
    # In a real implementation, you'd perform actual validation tests
    
    try:
        if init_type == 'gguf':
            # Check if file has GGUF header
            with open(model_path, 'rb') as f:
                header = f.read(4)
                if header == b'GGUF':
                    return True
                
                # Some GGUF models might not have the magic at the start
                # Try to check file size and extension as a fallback
                if os.path.splitext(model_path)[1].lower() == '.gguf' and os.path.getsize(model_path) > 1000000:
                    return True
                
                return False
        
        elif init_type == 'ggml':
            # Check if file has GGML header
            with open(model_path, 'rb') as f:
                header = f.read(4)
                if header == b'ggml':
                    return True
                
                # Fallback check based on extension
                if os.path.splitext(model_path)[1].lower() in ['.ggml', '.bin'] and os.path.getsize(model_path) > 1000000:
                    return True
                
                return False
        
        elif init_type == 'pytorch':
            # Check for PyTorch file signature or extension
            if os.path.splitext(model_path)[1].lower() in ['.pt', '.pth']:
                return True
            return False
        
        elif init_type == 'transformers':
            # Check for HuggingFace structure
            model_dir = os.path.dirname(model_path)
            if os.path.exists(os.path.join(model_dir, 'config.json')):
                return True
            
            if os.path.exists(os.path.join(model_dir, 'model.safetensors')) or \
               os.path.exists(os.path.join(model_dir, 'pytorch_model.bin')):
                return True
            
            return False
        
        # Unknown initializer type
        return False
    
    except Exception as e:
        logger.error(f"Validation error with {init_type}: {e}")
        return False

def test_model(model_name, model_config, verbose=True):
    """
    Test a single model
    
    Returns:
    - dict: Test results including success status, detected type, recommended type, etc.
    """
    result = {
        "model_name": model_name,
        "success": False,
        "tested_at": time.time(),
        "detected_type": "Unknown",
        "recommended_type": None,
        "file_exists": False,
        "file_size_mb": 0,
        "error": None
    }
    
    try:
        model_path = model_config.get('model_path', 'Unknown')
        
        # Check if file exists
        if model_path == 'Unknown' or not os.path.exists(model_path):
            result["error"] = f"Model file not found at {model_path}"
            if verbose:
                print(f"ERROR: Model file not found for {model_name} at {model_path}")
            return result
        
        result["file_exists"] = True
        
        if verbose:
            print(f"Testing model: {model_name}")
            print(f"  Path: {model_path}")
        
        # Check file size
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        result["file_size_mb"] = round(size_mb, 2)
        
        if verbose:
            print(f"  - File size: {size_mb:.2f} MB")
        
        # Detect model type
        detected_type = detect_model_type(model_path)
        configured_type = model_config.get('model_type', 'Unknown')
        
        result["detected_type"] = detected_type
        result["configured_type"] = configured_type
        
        if verbose:
            print(f"  - Configured type: {configured_type}")
            print(f"  - Detected type: {detected_type}")
        
        # Check if there's a mismatch
        if detected_type != 'Unknown' and configured_type != 'Unknown' and detected_type != configured_type:
            if verbose:
                print(f"  ⚠️ WARNING: Model type mismatch. Configuration says {configured_type}, but detected {detected_type}")
                print(f"     Consider updating model configuration to match detected type.")
        
        # Try alternative initializers if needed
        initializers_to_try = [configured_type]
        if detected_type != 'Unknown' and detected_type not in initializers_to_try:
            initializers_to_try.append(detected_type)
        
        # Add fallback initializers
        for fallback in ['gguf', 'ggml', 'pytorch', 'transformers']:
            if fallback not in initializers_to_try and fallback != 'Unknown':
                initializers_to_try.append(fallback)
        
        # Remove any None or Unknown entries
        initializers_to_try = [init for init in initializers_to_try if init and init != 'Unknown']
        
        # Try initializers
        init_success = False
        successful_type = None
        
        for init_type in initializers_to_try:
            try:
                if verbose:
                    print(f"  - Trying initializer: {init_type}")
                # Just do a basic validation, don't fully load the model
                if validate_model_with_initializer(model_path, init_type):
                    init_success = True
                    successful_type = init_type
                    break
            except Exception as e:
                if verbose:
                    print(f"    Failed with error: {str(e)}")
        
        result["success"] = init_success
        result["recommended_type"] = successful_type
        
        if init_success:
            if verbose:
                print(f"  ✓ Model {model_name} validated successfully with {successful_type} initializer")
            if successful_type != configured_type and configured_type != 'Unknown':
                if verbose:
                    print(f"    Consider updating model configuration to use {successful_type} initializer instead of {configured_type}")
        else:
            result["error"] = f"Failed to validate with any initializer"
            if verbose:
                print(f"  ✗ Failed to validate model {model_name} with any initializer")
        
        # Additional info from config
        result["context_length"] = model_config.get('context_length', 'Unknown')
        
        if verbose:
            print(f"  - Context length: {model_config.get('context_length', 'Unknown')}")
            print("")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        if verbose:
            print(f"Error testing model {model_name}: {e}")
            traceback.print_exc()
        return result

def load_models_manually(verbose=True):
    """Load model configurations manually from JSON files"""
    try:
        import os
        import json
        
        # Try to get models directory from environment variable, or use default paths
        models_dir = os.environ.get("LYRA_MODELS_DIR", None)
        if not models_dir:
            # Try common model directories
            potential_dirs = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BigModes", "TT Models"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Models")
            ]
            for dir_path in potential_dirs:
                if os.path.exists(dir_path):
                    models_dir = dir_path
                    break
            # If none found, use the original path
            if not models_dir:
                models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                        "BigModes", "TT Models")
        
        if verbose:
            print(f"Looking for model configs in: {models_dir}")
            
        if not os.path.exists(models_dir):
            if verbose:
                print(f"Models directory not found: {models_dir}")
            return {}
            
        all_models = {}
        for file in os.listdir(models_dir):
            if file.endswith('.json'):
                config_path = os.path.join(models_dir, file)
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    model_name = config.get('name', os.path.splitext(file)[0])
                    all_models[model_name] = config
                    if verbose:
                        print(f"Loaded config for model: {model_name}")
                except Exception as config_err:
                    if verbose:
                        print(f"Error loading config {file}: {config_err}")
        return all_models
    except Exception as config_loading_err:  # Fixed: Properly name exception variable
        if verbose:
            print(f"Error with manual config loading: {config_loading_err}")
        return {}

def test_models(model_names=None, force_retest=False, verbose=True):
    """
    Test multiple models and save results
    
    Args:
    - model_names: List of model names to test, or None to test all
    - force_retest: If True, retest even if previously tested
    - verbose: If True, print detailed output
    
    Returns:
    - dict: Results of tests
    """
    try:
        # Import here to avoid circular imports
        from modules.model_manager import ModelManager
        
        if verbose:
            print("Testing model initialization...")
        
        # Try to load models through ModelManager first
        all_models = {}
        try:
            model_manager = ModelManager()
            if verbose:
                print("ModelManager attributes:", dir(model_manager))
            
            # Try to find any attribute that could be a model config dictionary
            for attr_name in dir(model_manager):
                if attr_name.startswith('_'):
                    continue  # Skip private attributes
                try:
                    attr = getattr(model_manager, attr_name)
                    if isinstance(attr, dict) and len(attr) > 0:
                        # Check if this looks like a model config dict
                        try:
                            first_key = next(iter(attr))
                            first_value = attr[first_key]
                            if isinstance(first_value, dict) and ('model_path' in first_value or 'name' in first_value):
                                if verbose:
                                    print(f"Found model configurations in attribute: {attr_name}")
                                all_models = attr
                                break
                        except (StopIteration, TypeError, KeyError) as attr_exception:
                            # Handle case where the dictionary is empty or is not iterable
                            continue
                except Exception as attr_error:
                    if verbose:
                        print(f"Error accessing attribute {attr_name}: {attr_error}")
        except Exception as manager_error:
            if verbose:
                print(f"Error accessing ModelManager: {manager_error}")
        
        # If no models found through ModelManager, try manual loading
        if not all_models:
            if verbose:
                print("No model configurations found through ModelManager, trying manual loading...")
            all_models = load_models_manually(verbose)
        
        if not all_models:
            if verbose:
                print("ERROR: No models were found. Check your model directory.")
            return {"success": False, "error": "No models found"}
        
        # Filter to selected models if specified
        if model_names:
            models_to_test = {name: all_models[name] for name in model_names if name in all_models}
        else:
            models_to_test = all_models
        
        if verbose:
            print(f"Found {len(all_models)} models, will test {len(models_to_test)}.")
        
        # Load existing test results
        test_results = load_test_results()
        
        success_count = 0
        failed_count = 0
        
        # Test each model
        for model_name, model_config in models_to_test.items():
            # Skip if already tested and force_retest is False
            if not force_retest and model_name in test_results:
                if verbose:
                    print(f"Skipping model {model_name} - already tested")
                if test_results[model_name]["success"]:
                    success_count += 1
                else:
                    failed_count += 1
                continue
            
            try:
                # Test the model
                result = test_model(model_name, model_config, verbose)
                
                # Update test results
                test_results[model_name] = result
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as test_error:
                # Handle any unexpected errors during test_model call
                if verbose:
                    print(f"Error testing model {model_name}: {test_error}")
                test_results[model_name] = {
                    "model_name": model_name,
                    "success": False,
                    "tested_at": time.time(),
                    "error": str(test_error)
                }
                failed_count += 1
        
        # Save updated test results
        save_test_results(test_results)
        
        if verbose:
            print("\nModel testing complete!")
            print(f"Results: {success_count} models validated successfully, {failed_count} failed")
        
            return {
                "success": True,
                "total_models": len(models_to_test),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": test_results
            }
            
    except ImportError as import_error:
        if verbose:
            print(f"ERROR: Could not import necessary modules. {import_error}")
            print("Check your installation and make sure all dependencies are installed.")
        return {"success": False, "error": f"Import error: {str(import_error)}"}
        
    except Exception as general_error:
        if verbose:
            print(f"ERROR during model testing: {general_error}")
            traceback.print_exc()
        return {"success": False, "error": str(general_error)}

def check_untested_models(model_names=None):
    """
    Check if there are any untested models
    
    Args:
    - model_names: List of model names to check, or None to check all
    
    Returns:
    - list: Names of untested models
    """
    try:
        # Try to load model configurations
        all_models = load_models_manually(verbose=False)
        
        if not all_models:
            # If manual loading fails, try through ModelManager
            try:
                from modules.model_manager import ModelManager
                model_manager = ModelManager()
                
                # Try to find model configurations in any attribute
                for attr_name in dir(model_manager):
                    if attr_name.startswith('_'):
                        continue
                    try:
                        attr = getattr(model_manager, attr_name)
                        if isinstance(attr, dict) and len(attr) > 0:
                            # Check if this looks like a model config dict
                            try:
                                first_key = next(iter(attr))
                                first_value = attr[first_key]
                                if isinstance(first_value, dict) and ('model_path' in first_value or 'name' in first_value):
                                    all_models = attr
                                    break
                            except (StopIteration, KeyError, TypeError):
                                # Handle case where the dictionary might be empty or not iterable
                                continue
                    except Exception as attr_error:
                        logger.debug(f"Error examining attribute {attr_name}: {attr_error}")
            except Exception as manager_error:
                logger.error(f"Error finding model configurations: {manager_error}")
        
        if not all_models:
            logger.warning("No model configurations found")
            return []
        
        available_model_names = list(all_models.keys())
        models_to_check = model_names if model_names else available_model_names
        
        # Load test results
        test_results = load_test_results()
        
        # Find untested models
        untested_models = [name for name in models_to_check if name not in test_results]
        
        return untested_models
    
    except Exception as check_error:
        logger.error(f"Error checking untested models: {check_error}")
        return []

def main():
    """Command line interface for model testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lyra Model Testing Tool")
    parser.add_argument("--models", nargs="+", help="Specific models to test")
    parser.add_argument("--force", action="store_true", help="Force retest of all models")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    # Configure logging for command line use
    logging_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=logging_level)
    
    # Run tests
    test_models(args.models, args.force, not args.quiet)

if __name__ == "__main__":
    main()
