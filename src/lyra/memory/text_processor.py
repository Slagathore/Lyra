"""
Text processing utilities for efficient memory storage
"""
import re
import string
from typing import List, Dict, Any, Optional
import hashlib

class TextProcessor:
    """Process text for efficient memory storage"""
    
    def __init__(self):
        """Initialize the text processor"""
        # Common filler words to remove
        self.filler_words = {
            'um', 'uh', 'like', 'you know', 'actually', 'basically', 'literally',
            'just', 'so', 'anyway', 'i mean', 'well', 'right', 'okay'
        }
        
        # Common contractions
        self.contractions = {
            "aren't": "are not", "can't": "cannot", "couldn't": "could not",
            "didn't": "did not", "doesn't": "does not", "don't": "do not",
            "hadn't": "had not", "hasn't": "has not", "haven't": "have not",
            "he'd": "he would", "he'll": "he will", "he's": "he is",
            "i'd": "i would", "i'll": "i will", "i'm": "i am", "i've": "i have",
            "isn't": "is not", "let's": "let us", "mightn't": "might not",
            "mustn't": "must not", "shan't": "shall not", "she'd": "she would",
            "she'll": "she will", "she's": "she is", "shouldn't": "should not",
            "that's": "that is", "there's": "there is", "they'd": "they would",
            "they'll": "they will", "they're": "they are", "they've": "they have",
            "we'd": "we would", "we're": "we are", "we've": "we have",
            "weren't": "were not", "what'll": "what will", "what're": "what are",
            "what's": "what is", "what've": "what have", "where's": "where is",
            "who'd": "who would", "who'll": "who will", "who're": "who are",
            "who's": "who is", "who've": "who have", "won't": "will not",
            "wouldn't": "would not", "you'd": "you would", "you'll": "you will",
            "you're": "you are", "you've": "you have"
        }
        
    def normalize_text(self, text: str) -> str:
        """Normalize text by removing noise and standardizing format"""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Expand contractions
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def clean_for_memory(self, text: str, aggressive: bool = False) -> str:
        """Clean text for memory storage"""
        if not text:
            return ""
            
        # Basic normalization
        text = self.normalize_text(text)
        
        if aggressive:
            # Remove filler words
            for filler in self.filler_words:
                text = re.sub(r'\b' + filler + r'\b', '', text)
                
            # Remove punctuation except . ! ?
            punctuation_to_remove = string.punctuation.replace('.', '').replace('!', '').replace('?', '')
            for char in punctuation_to_remove:
                text = text.replace(char, '')
        
        # Remove excess whitespace again
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def extract_key_information(self, text: str) -> Dict[str, Any]:
        """Extract key information from text"""
        # This is a simplified implementation
        # A more sophisticated version would use NER and other NLP techniques
        
        result = {
            "entities": [],
            "keywords": [],
            "summary": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": "neutral"
        }
        
        # Simple entity extraction (names, locations)
        name_matches = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', text)
        if name_matches:
            result["entities"].extend(name_matches)
            
        # Simple keyword extraction (nouns)
        words = text.split()
        # This is very simplistic - a real implementation would use POS tagging
        result["keywords"] = [word for word in words if len(word) > 4][:10]
        
        # Simple sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'like']
        negative_words = ['bad', 'terrible', 'awful', 'sad', 'hate', 'dislike']
        
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        
        if pos_count > neg_count:
            result["sentiment"] = "positive"
        elif neg_count > pos_count:
            result["sentiment"] = "negative"
            
        return result
        
    def compute_memory_fingerprint(self, text: str) -> str:
        """Compute a fingerprint for deduplication"""
        # Normalize text first
        normalized_text = self.normalize_text(text)
        
        # Remove all punctuation and spaces for fingerprinting
        fingerprint_text = ''.join(c for c in normalized_text if c.isalnum())
        
        # Create hash
        return hashlib.md5(fingerprint_text.encode()).hexdigest()
        
    def check_duplicate(self, text: str, existing_texts: List[str], threshold: float = 0.8) -> bool:
        """Check if text is a duplicate of any existing text"""
        # Compute fingerprint
        fingerprint = self.compute_memory_fingerprint(text)
        
        # Compare with existing fingerprints
        for existing_text in existing_texts:
            existing_fingerprint = self.compute_memory_fingerprint(existing_text)
            
            # Simple similarity - real implementation would use Jaccard or cosine
            # This is just a placeholder for the concept
            common_chars = 0
            for i in range(min(len(fingerprint), len(existing_fingerprint))):
                if fingerprint[i] == existing_fingerprint[i]:
                    common_chars += 1
                    
            similarity = common_chars / max(len(fingerprint), len(existing_fingerprint))
            if similarity >= threshold:
                return True
                
        return False
        
    def compress_memory(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compress similar memories into summaries"""
        # Group memories by similarity
        # This is a simplified placeholder implementation
        
        if not memories:
            return []
            
        compressed = []
        processed_indices = set()
        
        for i, memory in enumerate(memories):
            if i in processed_indices:
                continue
                
            similar_memories = [memory]
            processed_indices.add(i)
            
            # Find similar memories
            for j, other_memory in enumerate(memories):
                if j in processed_indices or i == j:
                    continue
                    
                # Check similarity (simplified)
                if memory.get("category") == other_memory.get("category"):
                    content1 = memory.get("content", "")
                    content2 = other_memory.get("content", "")
                    
                    if self.check_duplicate(content1, [content2], threshold=0.7):
                        similar_memories.append(other_memory)
                        processed_indices.add(j)
            
            # If we found similar memories, compress them
            if len(similar_memories) > 1:
                # Create a compressed memory
                compressed_content = f"Combined memory from {len(similar_memories)} similar entries: "
                compressed_content += similar_memories[0].get("content", "")
                
                compressed.append({
                    "content": compressed_content,
                    "category": memory.get("category", "general"),
                    "importance": max(m.get("importance", 0.5) for m in similar_memories),
                    "timestamp": max(m.get("timestamp", "") for m in similar_memories),
                    "compressed": True,
                    "source_count": len(similar_memories)
                })
            else:
                # Just add the original memory
                compressed.append(memory)
                
        return compressed
