"""
Example of using your Qwen model through the OpenAI-compatible API
provided by oobabooga/text-generation-webui
"""
import openai
import json

# Configure the client to use the local API
client = openai.OpenAI(
    base_url="http://localhost:5000/v1",  # Default API URL from text-generation-webui
    api_key="dummy-key"  # Not actually used but required by the client
)

def chat_example():
    """Example of using the chat completions API"""
    print("\n=== CHAT EXAMPLE ===")
    
    # Create a chat completion
    response = client.chat.completions.create(
        model="Qwen2.5",  # This can be any name, it doesn't matter for the local API
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Write a short poem about artificial intelligence."}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    print(response.choices[0].message.content)

def json_example():
    """Example of using JSON mode for structured outputs"""
    print("\n=== JSON EXAMPLE ===")
    
    response = client.chat.completions.create(
        model="Qwen2.5",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
            {"role": "user", "content": "List three famous scientists and their contributions."}
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
        max_tokens=500
    )
    
    print(response.choices[0].message.content)
    data = json.loads(response.choices[0].message.content)
    print("\nParsed JSON:", json.dumps(data, indent=2))

def streaming_example():
    """Example of using streaming for real-time output"""
    print("\n=== STREAMING EXAMPLE ===")
    
    response = client.chat.completions.create(
        model="Qwen2.5",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Explain quantum computing in simple terms."}
        ],
        temperature=0.7,
        max_tokens=500,
        stream=True  # Enable streaming
    )
    
    print("Response: ", end="")
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    print("Testing Qwen2.5 model through the oobabooga API")
    print("Make sure the text-generation-webui is running with the --api flag")
    
    try:
        chat_example()
        json_example()
        streaming_example()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the text-generation-webui server is running with --api flag enabled")
        print("Run the run_qwen_webui.bat file in the oobabooga directory")
