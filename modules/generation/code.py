# ...existing code...

def generate_code(prompt, language="python", model_instance=None):
    try:
        # Enhanced prompt template for better code generation
        code_prompt = f"""
Please write code in {language} that accomplishes the following task:
{prompt}

Provide only the code without any explanations or markdown formatting.
"""
        # Use the model instance if provided
        if model_instance and hasattr(model_instance, 'generate'):
            response = model_instance.generate(code_prompt, max_tokens=2048)
        else:
            # Use the global model if available
            from modules.model import get_model
            model = get_model()
            if model:
                response = model.generate(code_prompt, max_tokens=2048)
            else:
                response = "Model not loaded. Cannot generate code."
                
        # Extract just the code from the response
        code_pattern = re.compile(r'```(?:\w+)?\s*([\s\S]+?)\s*```')
        code_match = code_pattern.search(response)
        
        if code_match:
            return code_match.group(1).strip()
        
        # If no code block found, return the whole response
        # Remove markdown formatting if present
        response = response.replace('```' + language, '').replace('```', '')
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return f"Error generating code: {str(e)}"

# ...existing code...
