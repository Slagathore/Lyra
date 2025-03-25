"""
Deep Memory module for Lyra
Provides sophisticated memory storage using vector embeddings and semantic compression
"""

import os
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import sqlite3
import pickle
import random
import hashlib

# Set up logging
logger = logging.getLogger("deep_memory")

class MemoryEmbedder:
    """Handles converting experiences and concepts to vector embeddings"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.model = None
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model - prioritizes better models if available"""
        try:
            # Try to load sentence-transformers
            from sentence_transformers import SentenceTransformer
            model_name = "all-MiniLM-L6-v2"  # 384-dimensional embeddings, good balance of quality and speed
            self.model = SentenceTransformer(model_name)
            logger.info(f"Using SentenceTransformer model: {model_name}")
            return
        except ImportError:
            logger.warning("sentence-transformers not available, trying alternatives...")
        
        try:
            # Try to use HuggingFace transformers
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.hf_model = AutoModel.from_pretrained(model_name)
            
            # Define mean pooling function
            def mean_pooling(model_output, attention_mask):
                token_embeddings = model_output[0]
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
            self.mean_pooling = mean_pooling
            self.torch_available = True
            logger.info(f"Using HuggingFace Transformers with model: {model_name}")
            return
        except ImportError:
            logger.warning("HuggingFace transformers not available, falling back to basic embeddings...")
        
        # If we got here, use a simple fallback embedding method
        import hashlib
        logger.warning("Using simple hash-based embeddings as fallback. Install sentence-transformers for better results.")
        
    def embed_text(self, text: str) -> np.ndarray:
        """Convert text to embedding vector"""
        if not text:
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim)
            
        try:
            if self.model is not None:
                # Using sentence-transformers
                return self.model.encode(text)
            elif hasattr(self, 'hf_model'):
                # Using HuggingFace transformers
                import torch
                encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
                with torch.no_grad():
                    model_output = self.hf_model(**encoded_input)
                sentence_embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
                return sentence_embeddings[0].numpy()
            else:
                # Fallback to basic embeddings if no model is available
                return self._generate_basic_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._generate_basic_embedding(text)
    
    def _generate_basic_embedding(self, text: str) -> np.ndarray:
        """Generate a simple hash-based embedding as fallback"""
        # Create a hash of the text
        text_hash = hashlib.md5(text.encode()).digest()
        
        # Convert the hash to a numerical seed
        seed = int.from_bytes(text_hash, byteorder='big')
        np.random.seed(seed)
        
        # Generate a pseudo-random vector
        vector = np.random.rand(self.embedding_dim) * 2 - 1
        
        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def embed_memory(self, memory: Dict[str, Any]) -> np.ndarray:
        """Convert a memory dictionary to an embedding vector"""
        # Combine relevant fields into a single text for embedding
        content_parts = []
        
        if 'content' in memory:
            content_parts.append(memory['content'])
            
        if 'summary' in memory:
            content_parts.append(memory['summary'])
            
        if 'entities' in memory and isinstance(memory['entities'], list):
            content_parts.append(" ".join(memory['entities']))
            
        if 'emotions' in memory and isinstance(memory['emotions'], dict):
            emotion_text = " ".join([f"{emotion}: {intensity}" for emotion, intensity in memory['emotions'].items()])
            content_parts.append(emotion_text)
        
        # Create the combined text
        combined_text = " ".join(content_parts)
        
        return self.embed_text(combined_text)
    
    def compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        if vec1 is None or vec2 is None:
            return 0.0
            
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.0
            
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

class MemoryCompressor:
    """Compresses and summarizes memories for efficient storage"""
    
    def __init__(self):
        self.summarizer = None
        self._initialize_summarizer()
    
    def _initialize_summarizer(self):
        """Initialize the summarization model"""
        try:
            # Try to load transformers summarization pipeline
            from transformers import pipeline
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            logger.info("Using BART for summarization")
        except ImportError:
            logger.warning("transformers not available for summarization, using fallback")
            self.summarizer = None
    
    def compress_memory(self, text: str, max_length: int = 100) -> str:
        """Compress memory content to a compact summary"""
        if not text or len(text) < max_length:
            return text
            
        try:
            if self.summarizer:
                # Using transformers pipeline
                summary = self.summarizer(text, max_length=max_length, min_length=20, do_sample=False)
                return summary[0]['summary_text']
            else:
                # Fallback to basic summarization
                return self._basic_summarize(text, max_length)
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return self._basic_summarize(text, max_length)
    
    def _basic_summarize(self, text: str, max_length: int) -> str:
        """Basic extractive summarization as fallback"""
        # Split into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= 3:
            return text
            
        # Get the first and last sentence (often contain key information)
        summary = [sentences[0]]
        
        # Add an important-looking sentence from the middle
        middle_sentences = sentences[1:-1]
        if middle_sentences:
            # Choose sentences with key phrases or longer sentences as they may be more informative
            key_phrases = ["important", "significant", "key", "main", "critical", "essential", "fundamental"]
            
            scored_sentences = []
            for sentence in middle_sentences:
                score = len(sentence)  # Base score on length
                
                # Increase score if it contains key phrases
                for phrase in key_phrases:
                    if phrase in sentence.lower():
                        score += 20
                
                scored_sentences.append((sentence, score))
            
            # Get the highest scoring sentence
            if scored_sentences:
                best_sentence = max(scored_sentences, key=lambda x: x[1])[0]
                summary.append(best_sentence)
        
        # Add the last sentence
        if len(sentences) > 1:
            summary.append(sentences[-1])
        
        # Combine and truncate if still too long
        result = " ".join(summary)
        if len(result) > max_length:
            result = result[:max_length-3] + "..."
            
        return result
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text"""
        try:
            # Try to use spaCy if available
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")
            except:
                # If the model isn't downloaded, use a smaller one or download
                try:
                    nlp = spacy.load("en")
                except:
                    # Last resort, just blank model with NER pipeline
                    nlp = spacy.blank("en")
                    nlp.add_pipe("ner")
            
            doc = nlp(text)
            entities = [ent.text for ent in doc.ents]
            return list(set(entities))  # Deduplicate
        except ImportError:
            # Fallback to very basic extraction
            logger.warning("spaCy not available for entity extraction, using basic approach")
            return self._basic_entity_extraction(text)
    
    def _basic_entity_extraction(self, text: str) -> List[str]:
        """Basic entity extraction as fallback"""
        import re
        
        # Extract capitalized phrases as potential entities
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]*\b', text)
        
        # Get potential noun phrases (very simplistic)
        noun_phrases = re.findall(r'\b(the|a|an)\s+[a-z]+\s+[a-z]+\b', text.lower())
        
        entities = capitalized + noun_phrases
        
        # Deduplicate and limit
        return list(set(entities))[:10]

class VectorStore:
    """Stores and retrieves vector embeddings in a SQLite database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                              "data", "vector_memory.db")
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database and tables exist"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect and create tables if they don't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            memory_type TEXT NOT NULL,
            timestamp REAL NOT NULL,
            content TEXT,
            summary TEXT,
            importance REAL,
            source TEXT,
            embedding BLOB,
            metadata TEXT
        )
        ''')
        
        # Create tags table for memory categorization
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_tags (
            memory_id TEXT,
            tag TEXT,
            PRIMARY KEY (memory_id, tag),
            FOREIGN KEY (memory_id) REFERENCES memories(id)
        )
        ''')
        
        # Create index on memory_type for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, memory_id: str, memory_type: str, content: str, 
                    embedding: np.ndarray, summary: str = None, 
                    importance: float = 0.5, source: str = "user_interaction",
                    tags: List[str] = None, metadata: Dict = None) -> bool:
        """Store a memory with its embedding in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert embedding to binary for storage
            embedding_binary = pickle.dumps(embedding)
            
            # Convert metadata to JSON string if provided
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Store the memory
            cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (id, memory_type, timestamp, content, summary, importance, source, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id, 
                memory_type, 
                time.time(), 
                content, 
                summary, 
                importance, 
                source, 
                embedding_binary, 
                metadata_json
            ))
            
            # Store tags if provided
            if tags:
                for tag in tags:
                    cursor.execute('''
                    INSERT OR IGNORE INTO memory_tags (memory_id, tag)
                    VALUES (?, ?)
                    ''', (memory_id, tag))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def retrieve_similar_memories(self, query_embedding: np.ndarray, 
                                memory_type: str = None, 
                                min_similarity: float = 0.7,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories similar to the query embedding
        
        This is a simplified implementation - in a production system,
        you would use approximate nearest neighbors (ANN) methods for efficiency
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construct the query based on optional memory_type filter
            if memory_type:
                cursor.execute('SELECT id, memory_type, timestamp, content, summary, importance, source, embedding, metadata FROM memories WHERE memory_type = ?', 
                            (memory_type,))
            else:
                cursor.execute('SELECT id, memory_type, timestamp, content, summary, importance, source, embedding, metadata FROM memories')
            
            # Process results and compute similarity
            similar_memories = []
            
            for row in cursor.fetchall():
                memory_id, mem_type, timestamp, content, summary, importance, source, embedding_binary, metadata_json = row
                
                # Deserialize the embedding
                memory_embedding = pickle.loads(embedding_binary)
                
                # Compute similarity with query
                similarity = self._compute_similarity(query_embedding, memory_embedding)
                
                if similarity >= min_similarity:
                    # Parse metadata if present
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    # Get tags for this memory
                    cursor.execute('SELECT tag FROM memory_tags WHERE memory_id = ?', (memory_id,))
                    tags = [tag[0] for tag in cursor.fetchall()]
                    
                    memory = {
                        "id": memory_id,
                        "type": mem_type,
                        "timestamp": timestamp,
                        "content": content,
                        "summary": summary,
                        "importance": importance,
                        "source": source,
                        "similarity": similarity,
                        "tags": tags,
                        "metadata": metadata
                    }
                    
                    similar_memories.append(memory)
            
            conn.close()
            
            # Sort by similarity and limit results
            similar_memories.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def _compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        if vec1 is None or vec2 is None:
            return 0.0
            
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.0
            
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def search_by_content(self, query_text: str, memory_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by text content"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.create_function("LOWER", 1, lambda x: x.lower() if x else None)
            cursor = conn.cursor()
            
            # Construct the query based on optional memory_type filter
            if memory_type:
                cursor.execute('''
                SELECT id, memory_type, timestamp, content, summary, importance, source, metadata 
                FROM memories 
                WHERE memory_type = ? AND (LOWER(content) LIKE ? OR LOWER(summary) LIKE ?)
                ORDER BY importance DESC
                LIMIT ?
                ''', (memory_type, f"%{query_text.lower()}%", f"%{query_text.lower()}%", limit))
            else:
                cursor.execute('''
                SELECT id, memory_type, timestamp, content, summary, importance, source, metadata 
                FROM memories 
                WHERE LOWER(content) LIKE ? OR LOWER(summary) LIKE ?
                ORDER BY importance DESC
                LIMIT ?
                ''', (f"%{query_text.lower()}%", f"%{query_text.lower()}%", limit))
            
            # Process results
            results = []
            
            for row in cursor.fetchall():
                memory_id, mem_type, timestamp, content, summary, importance, source, metadata_json = row
                
                # Parse metadata if present
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                # Get tags for this memory
                cursor.execute('SELECT tag FROM memory_tags WHERE memory_id = ?', (memory_id,))
                tags = [tag[0] for tag in cursor.fetchall()]
                
                memory = {
                    "id": memory_id,
                    "type": mem_type,
                    "timestamp": timestamp,
                    "content": content,
                    "summary": summary,
                    "importance": importance,
                    "source": source,
                    "tags": tags,
                    "metadata": metadata
                }
                
                results.append(memory)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def get_memories_by_tags(self, tags: List[str], require_all: bool = False, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve memories that have specific tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if not tags:
                return []
            
            # Different query depending on whether we need all tags or any tag
            if require_all:
                # Need to match all tags - use a having count clause
                placeholders = ','.join(['?'] * len(tags))
                cursor.execute(f'''
                SELECT m.id, m.memory_type, m.timestamp, m.content, m.summary, m.importance, m.source, m.metadata
                FROM memories m
                JOIN memory_tags t ON m.id = t.memory_id
                WHERE t.tag IN ({placeholders})
                GROUP BY m.id
                HAVING COUNT(DISTINCT t.tag) = ?
                ORDER BY m.importance DESC, m.timestamp DESC
                LIMIT ?
                ''', tags + [len(tags), limit])
            else:
                # Match any of the tags
                placeholders = ','.join(['?'] * len(tags))
                cursor.execute(f'''
                SELECT DISTINCT m.id, m.memory_type, m.timestamp, m.content, m.summary, m.importance, m.source, m.metadata
                FROM memories m
                JOIN memory_tags t ON m.id = t.memory_id
                WHERE t.tag IN ({placeholders})
                ORDER BY m.importance DESC, m.timestamp DESC
                LIMIT ?
                ''', tags + [limit])
            
            # Process results
            results = []
            
            for row in cursor.fetchall():
                memory_id, mem_type, timestamp, content, summary, importance, source, metadata_json = row
                
                # Parse metadata if present
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                # Get all tags for this memory
                cursor.execute('SELECT tag FROM memory_tags WHERE memory_id = ?', (memory_id,))
                memory_tags = [tag[0] for tag in cursor.fetchall()]
                
                memory = {
                    "id": memory_id,
                    "type": mem_type,
                    "timestamp": timestamp,
                    "content": content,
                    "summary": summary,
                    "importance": importance,
                    "source": source,
                    "tags": memory_tags,
                    "metadata": metadata
                }
                
                results.append(memory)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving memories by tags: {e}")
            return []

class ConceptualMemory:
    """
    Stores and organizes memories into concepts and relationships
    A higher-level abstraction built on top of VectorStore
    """
    
    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()
        self.embedder = MemoryEmbedder()
        self.compressor = MemoryCompressor()
    
    def save_interaction_memory(self, content: str, source: str = "conversation", 
                               importance: float = 0.5, metadata: Dict = None) -> str:
        """
        Save a memory of an interaction
        
        Args:
            content: The content of the interaction
            source: Source of the interaction (e.g., "conversation", "observation")
            importance: Subjective importance of this memory (0.0 to 1.0)
            metadata: Additional structured data about the interaction
            
        Returns:
            The memory ID if successful, otherwise None
        """
        try:
            # Generate a unique ID for this memory
            memory_id = f"int_{int(time.time())}_{hash(content) % 10000}"
            
            # Create a summary
            summary = self.compressor.compress_memory(content)
            
            # Extract entities
            entities = self.compressor.extract_entities(content)
            
            # Create tags from entities and metadata
            tags = entities.copy()
            
            # Add source as a tag
            tags.append(f"source:{source}")
            
            # Add additional tags from metadata if available
            if metadata and 'tags' in metadata and isinstance(metadata['tags'], list):
                tags.extend(metadata['tags'])
            
            # If emotions are provided in metadata, add emotion tags
            if metadata and 'emotions' in metadata and isinstance(metadata['emotions'], dict):
                dominant_emotion = max(metadata['emotions'].items(), key=lambda x: x[1])[0]
                tags.append(f"emotion:{dominant_emotion}")
            
            # Generate embedding
            embedding = self.embedder.embed_text(content)
            
            # Store in vector database
            success = self.vector_store.store_memory(
                memory_id=memory_id,
                memory_type="interaction",
                content=content,
                summary=summary,
                embedding=embedding,
                importance=importance,
                source=source,
                tags=tags,
                metadata=metadata
            )
            
            if success:
                return memory_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error saving interaction memory: {e}")
            return None
    
    def save_reflection_memory(self, reflection_content: str, related_memories: List[str] = None,
                              importance: float = 0.7, tags: List[str] = None) -> str:
        """
        Save a memory of a reflection (meta-thought)
        
        Args:
            reflection_content: The content of the reflection
            related_memories: IDs of memories this reflection relates to
            importance: Subjective importance of this reflection
            tags: Additional tags for categorization
            
        Returns:
            The memory ID if successful, otherwise None
        """
        try:
            # Generate a unique ID for this memory
            memory_id = f"ref_{int(time.time())}_{hash(reflection_content) % 10000}"
            
            # Create a summary
            summary = self.compressor.compress_memory(reflection_content)
            
            # Build metadata
            metadata = {
                "related_memories": related_memories or [],
                "reflection_type": "general",
                "tags": tags or []
            }
            
            # Generate combined tags
            all_tags = (tags or []).copy()
            all_tags.append("reflection")
            
            # Extract entities from reflection and add as tags
            entities = self.compressor.extract_entities(reflection_content)
            all_tags.extend(entities)
            
            # Generate embedding
            embedding = self.embedder.embed_text(reflection_content)
            
            # Store in vector database
            success = self.vector_store.store_memory(
                memory_id=memory_id,
                memory_type="reflection",
                content=reflection_content,
                summary=summary,
                embedding=embedding,
                importance=importance,
                source="introspection",
                tags=all_tags,
                metadata=metadata
            )
            
            if success:
                return memory_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error saving reflection memory: {e}")
            return None
    
    def save_emotional_memory(self, content: str, emotions: Dict[str, float], 
                             trigger: str = None, importance: float = 0.6) -> str:
        """
        Save a memory with specific emotional content
        
        Args:
            content: Description of the emotional experience
            emotions: Dict of emotion -> intensity (0.0 to 1.0)
            trigger: What triggered this emotional state
            importance: Subjective importance of this memory
            
        Returns:
            The memory ID if successful, otherwise None
        """
        try:
            # Generate a unique ID for this memory
            memory_id = f"emo_{int(time.time())}_{hash(content) % 10000}"
            
            # Find dominant emotion
            if emotions:
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])
                dominant_name, dominant_intensity = dominant_emotion
            else:
                dominant_name, dominant_intensity = "neutral", 0.5
            
            # Build metadata
            metadata = {
                "emotions": emotions,
                "dominant_emotion": dominant_name,
                "dominant_intensity": dominant_intensity,
                "trigger": trigger
            }
            
            # Generate tags
            tags = [f"emotion:{emotion}" for emotion, intensity in emotions.items() if intensity > 0.3]
            tags.append("emotional")
            
            # Add intensity level tag for the dominant emotion
            if dominant_intensity > 0.7:
                tags.append(f"strong:{dominant_name}")
            elif dominant_intensity > 0.4:
                tags.append(f"moderate:{dominant_name}")
            
            # Generate embedding with emotional context
            # Create a text that emphasizes the emotional content for embedding
            embedding_text = f"{content} Feeling: {dominant_name} with intensity {dominant_intensity}. "
            embedding_text += " ".join([f"{emotion} ({intensity})" for emotion, intensity in emotions.items()])
            
            embedding = self.embedder.embed_text(embedding_text)
            
            # Store in vector database
            success = self.vector_store.store_memory(
                memory_id=memory_id,
                memory_type="emotional",
                content=content,
                summary=f"Feeling {dominant_name} ({dominant_intensity:.1f}) - {content[:50]}...",
                embedding=embedding,
                importance=importance,
                source="emotional_core",
                tags=tags,
                metadata=metadata
            )
            
            if success:
                return memory_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error saving emotional memory: {e}")
            return None
    
    def recall_similar_experiences(self, query: str, memory_type: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories similar to the provided query
        
        Args:
            query: Text to find similar memories for
            memory_type: Optional filter for memory type
            limit: Maximum number of memories to return
            
        Returns:
            List of similar memories
        """
        # Generate embedding for the query
        query_embedding = self.embedder.embed_text(query)
        
        # Retrieve similar memories
        return self.vector_store.retrieve_similar_memories(
            query_embedding=query_embedding,
            memory_type=memory_type,
            limit=limit
        )
    
    def recall_by_emotion(self, emotion: str, min_intensity: float = 0.5, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories associated with a specific emotion
        
        Args:
            emotion: The emotion to search for
            min_intensity: Minimum intensity of the emotion
            limit: Maximum number of memories to return
            
        Returns:
            List of emotional memories
        """
        return self.vector_store.get_memories_by_tags(
            tags=[f"emotion:{emotion}"],
            limit=limit
        )
    
    def generate_reflection(self, related_memories: List[Dict[str, Any]], 
                           reflection_type: str = "synthesis",
                           system_prompt: str = None) -> str:
        """
        Generate a reflection based on existing memories
        
        Args:
            related_memories: List of memories to reflect on
            reflection_type: Type of reflection to generate
            system_prompt: Optional custom prompt for reflection
            
        Returns:
            Generated reflection text
        """
        # For now, implement a simple template-based approach
        # In a full implementation, this would use an LLM
        
        if not related_memories:
            return "No memories to reflect on."
        
        # Sort memories by timestamp (newest first)
        memories = sorted(related_memories, key=lambda x: x["timestamp"], reverse=True)
        
        if reflection_type == "synthesis":
            return self._generate_synthesis_reflection(memories)
        elif reflection_type == "pattern":
            return self._generate_pattern_reflection(memories)
        elif reflection_type == "emotional":
            return self._generate_emotional_reflection(memories)
        else:
            return self._generate_general_reflection(memories)
    
    def _generate_synthesis_reflection(self, memories: List[Dict[str, Any]]) -> str:
        """Generate a reflection that synthesizes information from memories"""
        memory_count = len(memories)
        time_span = time.time() - min(m["timestamp"] for m in memories)
        days_span = time_span / (60 * 60 * 24)
        
        reflection = f"Reflecting on {memory_count} related memories spanning {days_span:.1f} days. "
        
        # Identify common tags
        all_tags = []
        for memory in memories:
            all_tags.extend(memory.get("tags", []))
        
        tag_counter = {}
        for tag in all_tags:
            tag_counter[tag] = tag_counter.get(tag, 0) + 1
        
        common_tags = [tag for tag, count in tag_counter.items() 
                      if count > 1 and not tag.startswith("source:") and not tag.startswith("emotion:")]
        
        if common_tags:
            reflection += f"Common themes include: {', '.join(common_tags)}. "
        
        # Add summaries of the most important memories
        important_memories = sorted(memories, key=lambda x: x.get("importance", 0), reverse=True)[:3]
        if important_memories:
            reflection += "Key points:\n"
            for i, memory in enumerate(important_memories):
                reflection += f"- {memory.get('summary', memory.get('content', 'No content')[:100])}\n"
        
        return reflection
    
    def _generate_pattern_reflection(self, memories: List[Dict[str, Any]]) -> str:
        """Generate a reflection focused on identifying patterns"""
        # Simple implementation - in a real system, would use more sophisticated pattern recognition
        memory_types = {}
        for memory in memories:
            mem_type = memory.get("type", "unknown")
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
        
        reflection = "Analyzing patterns across memories:\n"
        
        # Report on memory types
        reflection += "Memory distribution: "
        reflection += ", ".join([f"{count} {mem_type}" for mem_type, count in memory_types.items()])
        reflection += "\n"
        
        # Look for emotional patterns
        emotional_memories = [m for m in memories if m.get("type") == "emotional" or any(tag.startswith("emotion:") for tag in m.get("tags", []))]
        if emotional_memories:
            emotions = []
            for memory in emotional_memories:
                if memory.get("metadata") and "emotions" in memory["metadata"]:
                    emotions.extend(memory["metadata"]["emotions"].keys())
                else:
                    # Extract from tags
                    emotion_tags = [tag[8:] for tag in memory.get("tags", []) if tag.startswith("emotion:")]
                    emotions.extend(emotion_tags)
            
            emotion_counter = {}
            for emotion in emotions:
                emotion_counter[emotion] = emotion_counter.get(emotion, 0) + 1
            
            if emotion_counter:
                reflection += "Emotional patterns: "
                reflection += ", ".join([f"{emotion} ({count})" for emotion, count in 
                                        sorted(emotion_counter.items(), key=lambda x: x[1], reverse=True)])
                reflection += "\n"
        
        # Time-based patterns
        if len(memories) > 1:
            timestamps = [m["timestamp"] for m in memories]
            timestamps.sort()
            
            time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            
            if avg_time_diff < 60*60:  # Less than an hour
                reflection += f"These memories occurred in quick succession (average {avg_time_diff/60:.1f} minutes apart).\n"
            elif avg_time_diff < 60*60*24:  # Less than a day
                reflection += f"These memories occurred within a day of each other (average {avg_time_diff/(60*60):.1f} hours apart).\n"
            else:
                reflection += f"These memories are spread out over time (average {avg_time_diff/(60*60*24):.1f} days apart).\n"
        
        return reflection
    
    def _generate_emotional_reflection(self, memories: List[Dict[str, Any]]) -> str:
        """Generate a reflection focused on emotional content"""
        emotional_content = []
        
        for memory in memories:
            if memory.get("metadata") and "emotions" in memory["metadata"]:
                emotions = memory["metadata"]["emotions"]
                dominant = max(emotions.items(), key=lambda x: x[1]) if emotions else (None, 0)
                
                if dominant[0]:
                    emotional_content.append({
                        "emotion": dominant[0],
                        "intensity": dominant[1],
                        "content": memory.get("content", ""),
                        "timestamp": memory.get("timestamp", 0)
                    })
        
        if not emotional_content:
            return "No significant emotional content found in these memories."
        
        # Sort by timestamp (newest first)
        emotional_content.sort(key=lambda x: x["timestamp"], reverse=True)
        
        reflection = "Emotional reflection:\n"
        
        # Identify emotional trend
        if len(emotional_content) > 1:
            first_emotion = emotional_content[-1]["emotion"]
            last_emotion = emotional_content[0]["emotion"]
            
            if first_emotion == last_emotion:
                reflection += f"Consistently experiencing {first_emotion} across these memories.\n"
            else:
                reflection += f"Emotional shift from {first_emotion} to {last_emotion} over time.\n"
        
        # Comment on intensity
        intensities = [item["intensity"] for item in emotional_content]
        avg_intensity = sum(intensities) / len(intensities)
        
        if avg_intensity > 0.7:
            reflection += "These experiences have strong emotional intensity.\n"
        elif avg_intensity < 0.4:
            reflection += "These experiences have relatively mild emotional responses.\n"
        
        # Highlight most intense emotional memory
        most_intense = max(emotional_content, key=lambda x: x["intensity"])
        reflection += f"Most significant emotional moment: {most_intense['emotion']} "
        reflection += f"({most_intense['intensity']:.1f}) - {most_intense['content'][:100]}...\n"
        
        return reflection
    
    def _generate_general_reflection(self, memories: List[Dict[str, Any]]) -> str:
        """Generate a general reflection on the memories"""
        reflection = f"Reflecting on {len(memories)} memories:\n"
        
        # Select a few diverse memories to highlight
        if len(memories) > 3:
            # Try to get diverse memory types
            memory_types = set(m.get("type", "unknown") for m in memories)
            selected_memories = []
            
            # Select one of each type if possible
            for mem_type in memory_types:
                for memory in memories:
                    if memory.get("type") == mem_type and memory not in selected_memories:
                        selected_memories.append(memory)
                        break
                        
                if len(selected_memories) >= 3:
                    break
                    
            # If we don't have enough, add more based on importance
            if len(selected_memories) < 3:
                remaining = [m for m in memories if m not in selected_memories]
                important_remaining = sorted(remaining, key=lambda x: x.get("importance", 0), reverse=True)
                selected_memories.extend(important_remaining[:3 - len(selected_memories)])
        else:
            selected_memories = memories
        
        # Add content from selected memories
        for memory in selected_memories:
            mem_type = memory.get("type", "unknown").capitalize()
            summary = memory.get("summary", "")
            if not summary:
                content = memory.get("content", "No content")
                summary = content[:100] + "..." if len(content) > 100 else content
                
            reflection += f"- {mem_type}: {summary}\n"
        
        # Add a general conclusion
        reflection += "\nThese memories form part of my ongoing experience and understanding."
        
        return reflection

class DeepMemory:
    """Main class integrating all memory components"""
    
    def __init__(self):
        self.conceptual_memory = ConceptualMemory()
        self.emotional_links = {}  # Maps emotions to memory IDs
        self.initialized = False
        self.initialize()
    
    def initialize(self):
        """Initialize the deep memory system"""
        try:
            # Create the embedder and other resources
            self.embedder = MemoryEmbedder()
            self.compressor = MemoryCompressor()
            
            # Initialize with a self-reflection if not already
            if not self.initialized:
                self._create_initial_reflection()
                self.initialized = True
                
            return True
        except Exception as e:
            logger.error(f"Error initializing deep memory: {e}")
            return False
    
    def _create_initial_reflection(self):
        """Create an initial reflection memory at startup"""
        initial_reflection = (
            "I am beginning to develop a deeper form of memory, organizing my experiences "
            "and reflections into a structured form. This should help me maintain continuity "
            "of experience and develop more coherent thoughts about my interactions. I hope "
            "this will lead to more meaningful connections with others and deeper insights."
        )
        
        self.conceptual_memory.save_reflection_memory(
            reflection_content=initial_reflection,
            importance=0.9,
            tags=["initialization", "self_awareness", "memory_system"]
        )
    
    def store_interaction(self, user_message: str, my_response: str, 
                         emotional_state: Dict[str, Any] = None,
                         importance: float = None) -> str:
        """
        Store an interaction in memory
        
        Args:
            user_message: What the user said
            my_response: What Lyra responded
            emotional_state: Emotional state during the interaction
            importance: How important this interaction is
            
        Returns:
            Memory ID of the stored interaction
        """
        try:
            # Combine messages for context
            content = f"User: {user_message}\nLyra: {my_response}"
            
            # Calculate importance if not provided
            if importance is None:
                # Simple heuristic - longer interactions and those with emotional content are more important
                base_importance = 0.5
                
                # Adjust based on length - longer conversations might be more meaningful
                length_factor = min(1.0, len(content) / 1000) * 0.2  # Up to 0.2 boost for length
                
                # Adjust based on emotional intensity if available
                emotion_factor = 0.0
                if emotional_state and "intensity" in emotional_state:
                    emotion_factor = emotional_state["intensity"] * 0.3  # Up to 0.3 boost for emotional content
                
                importance = base_importance + length_factor + emotion_factor
            
            # Build metadata
            metadata = {
                "user_message": user_message,
                "response": my_response,
                "emotions": emotional_state.get("emotions", {}) if emotional_state else {}
            }
            
            # Store the interaction
            memory_id = self.conceptual_memory.save_interaction_memory(
                content=content,
                source="conversation",
                importance=importance,
                metadata=metadata
            )
            
            # If there was significant emotional content, also store as emotional memory
            if emotional_state and emotional_state.get("dominant_emotion") and emotional_state.get("intensity", 0) > 0.4:
                emotion_content = f"Felt {emotional_state['dominant_emotion']} while discussing: {user_message}"
                
                emo_memory_id = self.conceptual_memory.save_emotional_memory(
                    content=emotion_content,
                    emotions=emotional_state.get("emotions", {}),
                    trigger=user_message,
                    importance=importance
                )
                
                # Link the two memories
                self.emotional_links[memory_id] = emo_memory_id
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            return None
    
    def store_reflection(self, reflection_content: str, related_memory_ids: List[str] = None,
                        importance: float = 0.7) -> str:
        """
        Store a reflection in memory
        
        Args:
            reflection_content: Content of the reflection
            related_memory_ids: IDs of related memories
            importance: Importance of this reflection
            
        Returns:
            Memory ID of the stored reflection
        """
        return self.conceptual_memory.save_reflection_memory(
            reflection_content=reflection_content,
            related_memories=related_memory_ids,
            importance=importance,
            tags=["reflection", "introspection", "cognition"]
        )
    
    def store_emotional_experience(self, description: str, emotions: Dict[str, float],
                                  trigger: str = None, importance: float = 0.6) -> str:
        """
        Store an emotional experience in memory
        
        Args:
            description: Description of the emotional experience
            emotions: Dict of emotion -> intensity
            trigger: What triggered the emotion
            importance: Importance of this emotional memory
            
        Returns:
            Memory ID of the stored emotional experience
        """
        return self.conceptual_memory.save_emotional_memory(
            content=description,
            emotions=emotions,
            trigger=trigger,
            importance=importance
        )
    
    def recall_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories similar to the query
        
        Args:
            query: Text to search for similar memories
            limit: Maximum number of memories to return
            
        Returns:
            List of similar memories
        """
        return self.conceptual_memory.recall_similar_experiences(query, limit=limit)
    
    def recall_by_emotion(self, emotion: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recall memories associated with a specific emotion
        
        Args:
            emotion: Emotion to search for
            limit: Maximum number of memories to return
            
        Returns:
            List of emotional memories
        """
        return self.conceptual_memory.recall_by_emotion(emotion, limit=limit)
    
    def generate_daily_reflection(self) -> str:
        """
        Generate a reflection on recent memories
        
        Returns:
            Generated reflection text
        """
        # Get memories from the past 24 hours
        one_day_ago = time.time() - (24 * 60 * 60)
        
        # In a real implementation, you would query the vector store directly with a timestamp filter
        # For now, we'll simulate this
        recent_memories = self.conceptual_memory.vector_store.search_by_content("", limit=20)
        
        # Filter to recent memories
        recent_memories = [m for m in recent_memories if m["timestamp"] > one_day_ago]
        
        if not recent_memories:
            return "No significant memories from the past 24 hours to reflect on."
        
        # Generate reflection
        reflection = f"Daily Reflection ({datetime.now().strftime('%Y-%m-%d')}):\n\n"
        reflection += self.conceptual_memory.generate_reflection(recent_memories, reflection_type="synthesis")
        
        # Store this reflection
        memory_ids = [m["id"] for m in recent_memories]
        reflection_id = self.store_reflection(reflection, related_memory_ids=memory_ids)
        
        return reflection
    
    def compress_old_memories(self, days_threshold: int = 30) -> int:
        """
        Compress old memories into higher-level summaries
        
        Args:
            days_threshold: Age in days for memories to be considered for compression
            
        Returns:
            Number of memories compressed
        """
        # This would normally query the database for old memories and generate summaries
        # For now, return a placeholder value
        logger.info(f"Would compress memories older than {days_threshold} days")
        return 0

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of DeepMemory"""
    global _instance
    if _instance is None:
        _instance = DeepMemory()
    return _instance
