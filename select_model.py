"""
Script to select which model to use as active
"""
import sys
from model_config import get_manager

def main():
    """Select a model as active"""
    if len(sys.argv) < 2:
        print("Usage: python select_model.py MODEL_NAME")
        print("Use list_models.bat to see available models")
        return
    
    model_name = sys.argv[1]
    manager = get_manager()
    
    # Try to find the model
    found = False
    for model in manager.models:
        if model.name.lower() == model_name.lower():
            found = True
            break
    
    if not found:
        # Check if partial name match
        matching_models = [m for m in manager.models 
                          if model_name.lower() in m.name.lower()]
        
        if not matching_models:
            print(f"No model found matching '{model_name}'")
            print("Use list_models.bat to see available models")
            return
        elif len(matching_models) == 1:
            model_name = matching_models[0].name
            print(f"Using closest match: {model_name}")
        else:
            print(f"Multiple models match '{model_name}':")
            for m in matching_models:
                print(f"  - {m.name}")
            print("Please specify a unique name")
            return
    
    # Set the active model
    if manager.set_active_model(model_name):
        active_model = manager.get_active_model()
        print(f"Active model set to: {active_model.name}")
        print(f"Model path: {active_model.path}")
        print(f"Chat format: {active_model.chat_format}")
        print(f"GPU layers: {active_model.n_gpu_layers}")
        
        # Print command to run the model
        print("\nTo run this model, use:")
        print("  run_active_model.bat")
    else:
        print(f"Failed to set active model to {model_name}")

if __name__ == "__main__":
    main()
