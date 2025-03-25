import os
import json
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any

# Try to import dependencies with fallbacks
try:
    from textblob import TextBlob
except ImportError:
    print("Warning: TextBlob not found. Sentiment analysis will be disabled.")
    class TextBlob:
        def __init__(self, text): 
            self.text = text
            self.sentiment = type('obj', (object,), {'polarity': 0.0, 'subjectivity': 0.0})

# Local imports with error handling
try:
    from lyra.memory.json_memory_manager import JSONMemoryManager
except ImportError:
    print("Warning: JSONMemoryManager not found. Using fallback implementation.")
    class JSONMemoryManager:
        def __init__(self, file_path): self.file_path = file_path
        def add_memory(self, entry): print(f"Would save to {self.file_path}: {entry}")

try:
    from lyra.memory.faiss_memory_manager import FAISSMemoryManager
except ImportError:
    print("Warning: FAISSMemoryManager not found. Using fallback implementation.")
    class FAISSMemoryManager:
        def __init__(self, dim=384, index_file=""): self.dim, self.index_file = dim, index_file
        def add_embedding(self, embedding, metadata): pass
        def search(self, query_embedding, k=5): return [], []
        def deduplicate_entries(self, entries): return entries

try:
    from lyra.memory.sql_memory_manager import log_conversation
except ImportError:
    print("Warning: SQL memory manager not found. Using fallback implementation.")
    def log_conversation(*args, **kwargs): print("SQL logging skipped (module not found)")

# Try to import LangChain, but prefer our local version first
try:
    from lyra.langchain_local_integration import create_conversation_chain
    print("Using local LangChain integration")
except ImportError:
    try:
        from lyra.langchain_integration import create_conversation_chain
        print("Using OpenAI LangChain integration")
    except ImportError:
        print("Warning: LangChain integration not found. Using fallback implementation.")
        def create_conversation_chain(): 
            return type('obj', (object,), {'run': lambda self, text: "No context available."})()

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: Sentence-transformers not found. Using random embeddings.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Import config
try:
    from lyra.config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: Config module not found. Using default settings.")

class CombinedMemoryManager:
    def __init__(self):
        """
        Initialize the combined memory manager that integrates multiple storage systems.
        """
        print("Initializing Combined Memory Manager...")
        json_file = os.path.join(os.getcwd(), "conversation_history.json")
        self.json_manager = JSONMemoryManager(file_path=json_file)
        self.faiss_manager = FAISSMemoryManager(dim=384, index_file="faiss_index.bin")
        
        # Use conversation chain based on config
        if CONFIG_AVAILABLE:
            config = get_config()
            use_local_llm = config.get("llm", "use_local_llm", True)
            model_path = config.get_llm_model_path() if use_local_llm else None
            self.conversation_chain = create_conversation_chain(model_path=model_path)
        else:
            self.conversation_chain = create_conversation_chain()
        
        # Load sentence transformer model for embeddings
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Get embedding model from config if available
                model_name = "all-MiniLM-L6-v2"
                if CONFIG_AVAILABLE:
                    model_name = get_config().get("memory", "embedding_model", model_name)
                
                self.embedding_model = SentenceTransformer(model_name)
                print(f"Sentence transformer model loaded successfully: {model_name}")
            except Exception as e:
                print(f"Error loading sentence transformer: {e}")
                
    def add_memory(self, user_message: str, bot_response: str, tags: Optional[List[str]] = None, conversation_id: Optional[str] = None):
        """
        Add a memory entry to all storage systems.
        
        Args:
            user_message: User's input message
            bot_response: Bot's response
            tags: Optional list of tags for categorization
            conversation_id: Optional conversation identifier
        """
        # Create memory entry
        timestamp = datetime.now().isoformat()
        memory_entry = {
            "user": user_message,
            "bot": bot_response,
            "timestamp": timestamp,
            "tags": tags or [],
            "conversation_id": conversation_id or "default"
        }
        
        # Add sentiment analysis
        try:
            sentiment = TextBlob(user_message).sentiment
            memory_entry["sentiment"] = {
                "polarity": sentiment.polarity,
                "subjectivity": sentiment.subjectivity
            }
        except:
            memory_entry["sentiment"] = {"polarity": 0.0, "subjectivity": 0.0}
        
        # Add to JSON storage
        try:
            self.json_manager.add_memory(memory_entry)
        except Exception as e:
            print(f"Error adding to JSON memory: {e}")
        
        # Create embedding and add to FAISS
        try:
            embedding = self.text_to_embedding(f"User: {user_message} Bot: {bot_response}")
            self.faiss_manager.add_embedding(embedding, memory_entry)
        except Exception as e:
            print(f"Error adding to FAISS: {e}")
        
    def text_to_embedding(self, text: str) -> np.ndarray:
        """
        Convert text to embedding vector.
        
        Args:
            text: Text to convert
            
        Returns:
            Embedding vector
        """
        # Use sentence transformer if available
        if self.embedding_model:
            try:
                return self.embedding_model.encode(text)
            except Exception as e:
                print(f"Error generating embedding: {e}")
                
        # Fallback to random vector (for testing only)
        print("Using fallback random embedding")
        return np.random.rand(384)
        
    def get_context(self, query_text: str, k: int = 5) -> Dict[str, Any]:
        """
        Get relevant context based on a query text.
        
        Args:
            query_text: Query text to find relevant context for
            k: Number of similar contexts to retrieve
            
        Returns:
            Dictionary with context and summary
        """
        try:
            query_embedding = self.text_to_embedding(query_text)
            distances, results = self.faiss_manager.search(query_embedding, k=k)

            if not results:
                return {"context": [], "summary": "No relevant context found."}

            current_time = datetime.now()
            for result in results:
                if "timestamp" in result:
                    try:
                        timestamp = datetime.fromisoformat(result["timestamp"])
                        age = (current_time - timestamp).total_seconds() / 3600
                        decay_factor = max(0, 1 - (age / 24))

                        if "important" in result.get("tags", []):
                            decay_factor = 1.0

                        if "score" in result:
                            result["score"] *= decay_factor
                    except:
                        pass

            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            unique_results = self.faiss_manager.deduplicate_entries(results)

            try:
                summary = self.conversation_chain.run(f"Summarize these past conversations: {unique_results}")
            except:
                summary = "Could not generate summary."

            return {"context": unique_results, "summary": summary}
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return {"context": [], "summary": "Error retrieving context."}

if __name__ == "__main__":
    cmm = CombinedMemoryManager()
    cmm.add_memory("Test", "Test response", ["important"])
    print("Memory test complete.")