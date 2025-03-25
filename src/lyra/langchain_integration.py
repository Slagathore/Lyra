from dotenv import load_dotenv
load_dotenv()

import os
# Updated imports for newer LangChain versions
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

def create_conversation_chain():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    
    # Use ChatOpenAI with a supported model, e.g., "chatgpt-4o-latest"
    llm = ChatOpenAI(
        temperature=0.7,
        openai_api_key=api_key,
        model_name="chatgpt-4o-latest"
    )
    
    # Use 'history' as the memory key
    memory = ConversationBufferMemory(memory_key="history")
    
    # Create the conversation chain
    conversation = ConversationChain(llm=llm, memory=memory)
    return conversation

if __name__ == "__main__":
    conversation_chain = create_conversation_chain()
    
    # Simulate a conversation turn
    user_input = "Hello, how are you?"
    response = conversation_chain.predict(input=user_input)
    print("Bot response:", response)
    
    # Continue the conversation
    user_input = "Tell me a short story."
    response = conversation_chain.predict(input=user_input)
    print("Bot response:", response)
