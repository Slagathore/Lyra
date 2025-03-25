"""
Simple API client for the llama-cpp-python server
"""
import requests
import sys
import time

def chat_with_api():
    print("=" * 50)
    print("API Client for Qwen 2.5 Model")
    print("Make sure the API server is running with api_server.bat")
    print("=" * 50)
    print("Type 'quit' to exit")
    print()
    
    history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        
        # Prepare the request
        url = "http://localhost:8000/v1/chat/completions"
        
        # Add user message to history
        history.append({"role": "user", "content": user_input})
        
        # Send the request
        try:
            print("AI: ", end="", flush=True)
            
            response = requests.post(
                url,
                json={
                    "model": "any-model-name",  # doesn't matter for local server
                    "messages": history,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                stream=True
            )
            
            if not response.ok:
                print(f"\nError: {response.status_code} - {response.text}")
                continue
            
            # Process the streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf8')
                    if line.startswith('data: '):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        
                        try:
                            import json
                            chunk = json.loads(data)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                print(content, end="", flush=True)
                                full_response += content
                        except:
                            pass
            
            print()  # Add a newline at the end
            
            # Add assistant response to history
            history.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            print(f"\nError connecting to API server: {e}")
            print("Make sure the API server is running (api_server.bat)")
            break

if __name__ == "__main__":
    chat_with_api()
