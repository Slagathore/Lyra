import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class FavoriteModelsManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.config_path = os.path.join(self.data_dir, "favorite_models.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Structure to hold favorite models by category
        self.favorites = {
            "chat": [],
            "text": [],
            "image": [],
            "code": [],
            "tts": []
        }
        
        # Load existing favorites
        self.load()
    
    def load(self) -> bool:
        """Load favorite models from disk"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Update favorites with loaded data
                for category in self.favorites.keys():
                    if category in data:
                        self.favorites[category] = data[category]
                        
                logger.info(f"Loaded favorite models from {self.config_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading favorite models: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save favorite models to disk"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2)
                
            logger.info(f"Saved favorite models to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving favorite models: {str(e)}")
            return False
    
    def add_favorite(self, category: str, model_path: str, model_info: Optional[Dict[str, Any]] = None) -> bool:
        """Add a model to favorites for a specific category"""
        try:
            if category not in self.favorites:
                logger.warning(f"Invalid category: {category}")
                return False
                
            # Create model entry
            model_entry = {
                "path": model_path,
                "name": os.path.basename(model_path)
            }
            
            # Add additional info if provided
            if model_info:
                model_entry.update({
                    "name": model_info.get("name", model_entry["name"]),
                    "type": model_info.get("type", "Unknown"),
                    "parameters": model_info.get("parameters", "Unknown"),
                    "size_gb": model_info.get("size_gb", 0)
                })
            
            # Check if model is already in favorites
            existing = [m for m in self.favorites[category] if m["path"] == model_path]
            if existing:
                # Update existing entry
                index = self.favorites[category].index(existing[0])
                self.favorites[category][index] = model_entry
            else:
                # Add new entry
                self.favorites[category].append(model_entry)
            
            # Save changes
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error adding favorite model: {str(e)}")
            return False
    
    def remove_favorite(self, category: str, model_path: str) -> bool:
        """Remove a model from favorites for a specific category"""
        try:
            if category not in self.favorites:
                logger.warning(f"Invalid category: {category}")
                return False
                
            # Find and remove the model
            self.favorites[category] = [m for m in self.favorites[category] if m["path"] != model_path]
            
            # Save changes
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error removing favorite model: {str(e)}")
            return False
    
    def get_favorites(self, category: str) -> List[Dict[str, Any]]:
        """Get favorite models for a specific category"""
        if category not in self.favorites:
            logger.warning(f"Invalid category: {category}")
            return []
            
        return self.favorites[category]
    
    def is_favorite(self, category: str, model_path: str) -> bool:
        """Check if a model is in favorites for a specific category"""
        if category not in self.favorites:
            return False
            
        return any(m["path"] == model_path for m in self.favorites[category])
    
    def get_all_favorites(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all favorite models"""
        return self.favorites

# Global instance
_favorite_models_manager = None

def get_favorite_models_manager():
    """Get the global favorite models manager instance"""
    global _favorite_models_manager
    if _favorite_models_manager is None:
        _favorite_models_manager = FavoriteModelsManager()
    return _favorite_models_manager
