# ...existing code...

def chat_completion(messages, model_instance=None, generation_settings=None):
    """Process a chat completion request with proper error handling"""
    try:
        # Use the provided model or get the global model
        if model_instance is None:
            from modules.model import get_model
            model_instance = get_model()
            
        if model_instance is None or not model_instance.model_loaded:
            return {"error": "Model not loaded. Please load a model first."}, 400
            
        # Apply default generation settings if not provided
        if generation_settings is None:
            generation_settings = {}
            
        # Process the messages
        response = model_instance.chat_completion(
            messages=messages,
            temperature=generation_settings.get('temperature', 0.7),
            top_p=generation_settings.get('top_p', 0.9),
            top_k=generation_settings.get('top_k', 40),
            max_tokens=generation_settings.get('max_tokens', 1024),
            presence_penalty=generation_settings.get('presence_penalty', 0.0),
            frequency_penalty=generation_settings.get('frequency_penalty', 0.0),
            stop=generation_settings.get('stop', None)
        )
        
        # Check for token limit errors
        if "error" in response and "max tokens" in response["error"].lower():
            # Try to recover by reducing history
            if len(messages) > 2:
                # Keep system message (if any) and last user message
                retained_messages = []
                if messages[0]["role"] == "system":
                    retained_messages.append(messages[0])
                retained_messages.append(messages[-1])
                
                # Try again with reduced history
                logger.warning("Reducing message history due to token limit")
                return chat_completion(retained_messages, model_instance, generation_settings)
            else:
                # If we're already at minimal history, return the error
                return response, 400
                
        return response, 200
        
    except Exception as e:
        error_msg = f"Error in chat completion: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}, 500

# ...existing code...