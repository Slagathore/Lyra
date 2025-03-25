"""
Simple client to interact with the llama-cpp-python REST API server
This can be used when the direct model loading doesn't work
"""
import requests
import sys
import json
import time

API_URL = "http://localhost:8000/v1"

def chat_with_api():
    print("Simple API client for llama-cpp-python server")
    print("Make sure the server is running with try_fallback_method.bat")
    print("Type 'quit' to exit\n")
    
    history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
            
        # Add user message to history
        history.append({"role": "user", "content": user_input})
        
        # Prepare the request
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "qwen2",  # The model name doesn't matter for local API
            "messages": history,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": True,  # Use streaming
        }
        
        # Stream the response
        print("AI: ", end="", flush=True)
        start_time = time.time()
        full_response = ""
        
        try:
            response = requests.post(
                f"{API_URL}/chat/completions",
                headers=headers,
                json=data,
                stream=True
            )
            
            if response.status_code != 200:
                print(f"\nError: API returned status code {response.status_code}")
                print(response.text)
                continue
                
            # Process the streaming response
            for line in response.iter_lines():
                if not line:
                    continue
                    
                # Parse the SSE data
                line = line.decode('utf-8')
                if not line.startswith('data: '):
                    continue
                    
                json_str = line[6:]  # Remove 'data: ' prefix
                
                if json_str == '[DONE]':
                    break
                    
                try:
                    chunk = json.loads(json_str)
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            print(content, end="", flush=True)
                            full_response += content
                except json.JSONDecodeError:
                    print(f"\nError parsing chunk: {json_str}")
                    
            # Add the assistant's response to history
            history.append({"role": "assistant", "content": full_response})
            
            print(f"\n[Generated {len(full_response)} chars in {time.time() - start_time:.2f} seconds]")
            print()
            
        except requests.exceptions.ConnectionError:
            print("\nError: Cannot connect to the API server")
            print("Make sure the server is running with try_fallback_method.bat")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            break

if __name__ == "__main__":
    chat_with_api()
