"""
FAISS Memory Manager for storing and retrieving embeddings
"""

import os
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import faiss
from pathlib import Path

class FAISSMemoryManager:
    def __init__(self, dim: int = 384, index_file: str = "faiss_index.bin"):
        """
        Initialize FAISS memory manager.
        
        Args:
            dim: Dimension of the embedding vectors
            index_file: Path to the FAISS index file
        """
        self.dim = dim
        self.index_file = Path(index_file)
        self.metadata = []
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.index_file) if os.path.dirname(self.index_file) else ".", exist_ok=True)
        
        # Create or load the index
        if self.index_file.exists():
            self.load_index()
        else:
            self.index = faiss.IndexFlatL2(dim)  # L2 distance index
            print(f"Created new FAISS index with dimension {dim}")
    
    def add_embedding(self, embedding: np.ndarray, metadata: dict):
        """
        Add embedding vector with associated metadata to the index.
        
        Args:
            embedding: The embedding vector
            metadata: Associated metadata dict
        """
        # Ensure the embedding is the right shape and type
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        embedding = embedding.astype(np.float32)
        
        # Add to the index
        self.index.add(embedding)
        
        # Store metadata
        metadata["index"] = self.index.ntotal - 1
        self.metadata.append(metadata)
        
        return self.index.ntotal - 1
        
    def search(self, query_embedding: np.ndarray, k: int = 5):
        """
        Search for similar vectors in the index.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            Tuple of (distances, results)
        """
        if self.index.ntotal == 0:
            return [], []
            
        # Ensure the query is the right shape and type
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype(np.float32)
        
        # Search the index
        k = min(k, self.index.ntotal)  # Don't request more results than we have
        distances, indices = self.index.search(query_embedding, k)
        
        print(f"Metadata length: {len(self.metadata)}")

        # Ensure indices are within bounds
        results = []
        for i in indices[0]:
            if i < len(self.metadata):
                results.append(self.metadata[i])
            else:
                results.append({})  # Fallback for out-of-range indices

        return distances[0].tolist(), results
        
    def deduplicate_entries(self, entries, threshold=0.95):
        """
        Remove duplicate entries based on content similarity.
        
        Args:
            entries: List of entries to deduplicate
            threshold: Similarity threshold
            
        Returns:
            Deduplicated list of entries
        """
        if not entries:
            return []
            
        # Simple deduplication - remove entries with same user message
        seen = set()
        unique = []
        
        for entry in entries:
            user_msg = entry.get("user", "")
            
            # Skip if empty or already seen
            if not user_msg or user_msg in seen:
                continue
                
            seen.add(user_msg)
            unique.append(entry)
            
        return unique
        
    def save_index(self):
        """Save the FAISS index and metadata to disk"""
        if not hasattr(self, 'index') or self.index is None:
            print("No index to save")
            return
            
        try:
            # Save the FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
            # Save the metadata
            metadata_file = self.index_file.with_suffix(".json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
                
            print(f"Saved index with {self.index.ntotal} entries")
        except Exception as e:
            print(f"Error saving index: {e}")
            
    def load_index(self):
        """Load the FAISS index and metadata from disk"""
        try:
            # Load the FAISS index
            self.index = faiss.read_index(str(self.index_file))
            
            # Load the metadata
            metadata_file = self.index_file.with_suffix(".json")
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            else:
                # If no metadata file exists, create empty metadata
                self.metadata = [{} for _ in range(self.index.ntotal)]
                
            print(f"Loaded index with {self.index.ntotal} entries and {len(self.metadata)} metadata entries")
        except Exception as e:
            print(f"Error loading index: {e}")
            # Create a new index as fallback
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadata = []

if __name__ == "__main__":
    # Test the FAISS memory manager
    manager = FAISSMemoryManager()
    
    # Add a test embedding
    test_vec = np.random.rand(384).astype(np.float32)
    manager.add_embedding(test_vec, {"text": "This is a test"})
    
    # Search for similar vectors
    distances, results = manager.search(test_vec, k=1)
    print(f"Search results: {results}")
    
    # Save the index
    manager.save_index()