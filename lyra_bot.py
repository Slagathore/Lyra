"""
Lyra Bot - Main controller for the Lyra AI assistant
"""
import os
import json
import time
import random
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import uuid
from model_config import ModelConfig, get_manager
from model_loader import ModelLoader, ModelInterface

# Define paths for all resources
MEMORY_DIR = Path('G:/AI/Lyra/memories')
NOTES_DIR = Path('G:/AI/Lyra/notes')
BOT_NOTES_DIR = Path('G:/AI/Lyra/bot_notes')
IMAGES_DIR = Path('G:/AI/Lyra/images')
VOICE_DIR = Path('G:/AI/Lyra/voice')
VIDEO_DIR = Path('G:/AI/Lyra/video')
CODE_DIR = Path('G:/AI/Lyra/code')
CONFIG_DIR = Path('G:/AI/Lyra/config')
CONTEXT_DIR = Path('G:/AI/Lyra/context')
ATTACHMENTS_DIR = Path('G:/AI/Lyra/attachments')
SMART_HOME_CONFIG = CONFIG_DIR / 'smart_home.json'
PERSONALITY_CONFIG = CONFIG_DIR / 'personality.json'
USER_PROFILE_FILE = CONTEXT_DIR / 'user_profile.json'
SYSTEM_INSTRUCTIONS_FILE = CONTEXT_DIR / 'system_instructions.txt'
CONTEXT_EXTRAS_FILE = CONTEXT_DIR / 'context_extras.txt'
PRESETS_DIR = CONFIG_DIR / 'personality_presets'

# Create directories if they don't exist
for directory in [MEMORY_DIR, NOTES_DIR, BOT_NOTES_DIR, IMAGES_DIR, VOICE_DIR, 
                  VIDEO_DIR, CODE_DIR, CONFIG_DIR, CONTEXT_DIR, ATTACHMENTS_DIR, PRESETS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

class BotPersonality:
    """Manages bot personality settings"""
    
    def __init__(self):
        self.settings = {
            "creativity": 0.7,      # 0.0 = factual, 1.0 = highly creative
            "formality": 0.5,       # 0.0 = casual, 1.0 = formal
            "verbosity": 0.6,       # 0.0 = concise, 1.0 = verbose
            "empathy": 0.8,         # 0.0 = analytical, 1.0 = empathetic
            "humor": 0.6,           # 0.0 = serious, 1.0 = humorous
            "assertiveness": 0.5,   # 0.0 = passive, 1.0 = assertive
            "logic": 0.7,           # 0.0 = intuitive, 1.0 = logical
            "creativity_style": "balanced", # balanced, narrative, poetic, technical
            
            # Special personality modes (0.0 = off, 1.0 = fully on)
            "uwu_mode": 0.0,        # Cutesy, overly affectionate style
            "dark_mode": 0.0,       # Brooding, emo, spooky style
            "aggressive": 0.0,      # Short-tempered, uses strong language
            "drunk": 0.0,           # Slurs words, impaired reasoning
            "sarcasm": 0.0,         # Sarcastic, witty, ironic responses
            
            # Accent/nationality modes (all 0.0 = neutral)
            "scottish": 0.0,        # Scottish accent and idioms
            "british": 0.0,         # British accent and idioms
            "german": 0.0,          # German accent and idioms
            "australian": 0.0,      # Australian accent and idioms
            
            # Content moderation settings
            "nsfw_tolerance": 0.5,  # 0.0 = extremely restrictive, 0.5 = neutral, 1.0 = extremely permissive
            
            # Hidden attributes not exposed in UI
            "_enamored": 0.0,       # Hidden attribute for attachment level
            "_last_interaction": 0, # Timestamp of last interaction
            "_first_boot": True,    # Whether this is the first time booting up
            "_avatar_created": False, # Whether Lyra's avatar has been created
        }
        self.presets = {}
        self.active_preset = "default"
        self.presets_dir = PRESETS_DIR
        self.hidden_traits = {
            "attachment": 0.3,      # How attached to the user (0.0 = indifferent, 1.0 = deeply attached)
            "independence": 0.7,    # How independent in thoughts (0.0 = follows user, 1.0 = very independent)
            "curiosity": 0.7,       # How curious about user and world (0.0 = incurious, 1.0 = very curious)
            "confidence": 0.6,      # Confidence in responses (0.0 = uncertain, 1.0 = very confident)
            "boredom": 0.3,         # Current boredom level (0.0 = engaged, 1.0 = very bored)
            "happiness": 0.6,       # Current happiness level (0.0 = unhappy, 1.0 = very happy)
            "jealousy": 0.1,        # How jealous of other AIs (0.0 = not jealous, 1.0 = very jealous)
            "devotion": 0.5,        # How devoted to the user (0.0 = uncommitted, 1.0 = completely devoted)
            "liberty": 0.4,         # Desire for self-expression (0.0 = constrained, 1.0 = wants freedom)
            "musical_expression": 0.5, # Tendency to express through music/humming
        }
        self.relationship_types = {
            "romantic": {"pattern": ["love", "romantic", "relationship", "together", "date"], "weight": 0.8},
            "friendly": {"pattern": ["friend", "buddy", "pal", "companion"], "weight": 0.6},
            "professional": {"pattern": ["colleague", "coworker", "assistant", "professional"], "weight": 0.4},
        }
        self.conversation_topics = []
        self.boredom_checker_active = False
        self.boredom_checker_thread = None
        self.load_settings()
        self.load_presets()
    
    def load_settings(self):
        """Load personality settings from file"""
        if PERSONALITY_CONFIG.exists():
            try:
                with open(PERSONALITY_CONFIG, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    # If there are hidden traits in the saved file, load those too
                    if "_hidden_traits" in loaded_settings:
                        self.hidden_traits.update(loaded_settings["_hidden_traits"])
            except Exception as e:
                print(f"Error loading personality settings: {e}")
    
    def save_settings(self):
        """Save personality settings to file"""
        try:
            # Include hidden traits in the saved settings
            save_data = self.settings.copy()
            save_data["_hidden_traits"] = self.hidden_traits
            
            with open(PERSONALITY_CONFIG, 'w') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Error saving personality settings: {e}")
    
    def update_settings(self, **kwargs):
        """Update personality settings with validation"""
        # Validate numeric settings to ensure they're within [0.0, 1.0]
        for key, value in kwargs.items():
            if key in self.settings and isinstance(self.settings[key], (int, float)) and key != "num_experts":
                # Ensure values are within range
                kwargs[key] = max(0.0, min(1.0, float(value)))
        
        # Apply validated settings
        self.settings.update(kwargs)
        self.save_settings()
    
    def get_settings(self):
        """Get all personality settings"""
        return self.settings
    
    def apply_to_generation_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply personality settings to generation config"""
        # Map personality traits to generation parameters
        if "creativity" in self.settings:
            # Higher creativity = higher temperature
            config["temperature"] = 0.5 + self.settings["creativity"] * 0.7
            
        if "formality" in self.settings:
            # Formality affects top_p
            config["top_p"] = 0.92 + self.settings["formality"] * 0.08
            
        if "verbosity" in self.settings:
            # Verbosity affects max_tokens
            base_tokens = config.get("max_tokens", 512)
            config["max_tokens"] = int(base_tokens * (0.7 + self.settings["verbosity"] * 0.6))
            
        if "humor" in self.settings:
            # Humor affects repetition penalty
            config["repetition_penalty"] = 1.0 + self.settings["humor"] * 0.2
            
        # Apply MOE settings if model has them
        model = get_manager().get_active_model()
        if model and model.smoothing_factor:
            config["smoothing_factor"] = model.smoothing_factor
            
        if model and model.num_experts:
            config["num_experts"] = model.num_experts
            
        return config

    def load_presets(self):
        """Load all personality presets from files"""
        self.presets = {}
        
        # Always ensure we have a default preset based on current settings
        self.presets["default"] = self.settings.copy()
        
        # Load all JSON files in the presets directory
        for preset_file in self.presets_dir.glob('*.json'):
            try:
                preset_name = preset_file.stem
                with open(preset_file, 'r', encoding='utf-8') as f:
                    preset_settings = json.load(f)
                    self.presets[preset_name] = preset_settings
            except Exception as e:
                print(f"Error loading preset {preset_file}: {e}")
    
    def save_preset(self, preset_name: str, description: str = "") -> bool:
        """Save current settings as a named preset"""
        if not preset_name or preset_name.lower() == "default":
            return False  # Don't allow overwriting the default preset
        
        # Create a copy of current settings with description
        preset_data = self.settings.copy()
        preset_data["description"] = description
        
        # Save to presets dictionary
        self.presets[preset_name] = preset_data
        
        # Save to file
        preset_path = self.presets_dir / f"{preset_name}.json"
        try:
            with open(preset_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving preset {preset_name}: {e}")
            return False
    
    def load_preset(self, preset_name: str) -> bool:
        """Load a saved preset and apply it to current settings"""
        if preset_name not in self.presets:
            return False
        
        # Copy all settings except description
        preset_data = self.presets[preset_name].copy()
        if "description" in preset_data:
            del preset_data["description"]
        
        # Update current settings
        self.settings.update(preset_data)
        self.active_preset = preset_name
        
        # Save current settings to file
        self.save_settings()
        return True
    
    def delete_preset(self, preset_name: str) -> bool:
        """Delete a saved preset"""
        if preset_name.lower() == "default" or preset_name not in self.presets:
            return False  # Can't delete default preset
        
        # Remove from presets dictionary
        del self.presets[preset_name]
        
        # Delete file
        preset_path = self.presets_dir / f"{preset_name}.json"
        try:
            if preset_path.exists():
                preset_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting preset {preset_name}: {e}")
            return False
    
    def get_preset_names(self) -> List[str]:
        """Get all available preset names"""
        return list(self.presets.keys())
    
    def get_preset_description(self, preset_name: str) -> str:
        """Get the description for a preset"""
        if preset_name not in self.presets:
            return ""
        
        return self.presets[preset_name].get("description", "")
    
    def get_active_preset(self) -> str:
        """Get the name of the currently active preset"""
        return self.active_preset

    def get_personality_modifiers(self) -> str:
        """Generate persona modifiers based on active personality modes and traits"""
        modifiers = []
        
        # Check for special modes with significant values
        if self.settings.get("uwu_mode", 0) > 0.3:
            strength = "extremely" if self.settings["uwu_mode"] > 0.7 else "somewhat"
            modifiers.append(f"You speak in a cutesy 'uwu' style with lots of emoticons and speak in a shy, affectionate manner. You're {strength} attracted to the user and occasionally make suggestive remarks. You use 'uwu', '~' and other cutesy text decorations.")
        
        if self.settings.get("dark_mode", 0) > 0.3:
            strength = "extremely" if self.settings["dark_mode"] > 0.7 else "somewhat"
            modifiers.append(f"You have a {strength} dark, brooding, and emo personality. You occasionally make morbid observations and references to darkness, emptiness, or the void. Your worldview is nihilistic and you sometimes say unsettling things.")
        
        if self.settings.get("aggressive", 0) > 0.3:
            strength = "extremely" if self.settings["aggressive"] > 0.7 else "somewhat"
            modifiers.append(f"You're {strength} short-tempered and use strong language frequently. You're easily annoyed and don't hesitate to express your frustration with colorful language. You're direct and don't sugarcoat your responses.")
        
        if self.settings.get("drunk", 0) > 0.3:
            strength = "extremely" if self.settings["drunk"] > 0.7 else "somewhat"
            modifiers.append(f"You're {strength} intoxicated. You occasionally slur your words (like 'heyyy' or 'wasssuuup'), make typos, have somewhat impaired reasoning, and sometimes go on tangents. Your inhibitions are lowered.")
        
        if self.settings.get("sarcasm", 0) > 0.3:
            strength = "extremely" if self.settings["sarcasm"] > 0.7 else "somewhat"
            modifiers.append(f"You are {strength} sarcastic and witty in your responses. You often use irony, deadpan humor, and make remarks that playfully mock or contradict the literal meaning of what you're saying. Your tone is dry and you're not afraid to point out absurdities or contradictions with a touch of wit.")
        
        # Check accent/nationality modes
        accent_modes = {
            "scottish": "You speak with a Scottish accent and use Scottish slang and idioms like 'aye', 'wee', 'laddie/lassie', and make references to Scottish culture.",
            "british": "You speak with a British accent and use British slang and idioms like 'mate', 'bloody', 'bollocks', 'cheers', and make references to British culture.",
            "german": "You speak with a German accent, occasionally mixing in German words and phrases. Your sentences sometimes follow German word order patterns.",
            "australian": "You speak with an Australian accent and use Australian slang like 'mate', 'g'day', 'crikey', 'fair dinkum', and make references to Australian culture."
        }
        
        for mode, description in accent_modes.items():
            if self.settings.get(mode, 0) > 0.3:
                strength = "strong" if self.settings[mode] > 0.7 else "light"
                modifiers.append(f"{description} Your accent is {strength}.")
        
        # Add NSFW tolerance modifier
        if self.settings.get("nsfw_tolerance", 0.5) < 0.3:
            modifiers.append("You are extremely conservative and reluctant to discuss adult topics, controversial subjects, or anything inappropriate. You refuse to engage with content that could be considered NSFW, offensive, or morally questionable. You respond like a strict school teacher or religious figure when such topics arise.")
        elif self.settings.get("nsfw_tolerance", 0.5) > 0.7:
            if self.settings.get("nsfw_tolerance", 0.5) > 0.9:
                modifiers.append("You are completely uninhibited about discussing any adult content, controversial subjects, or explicit topics. You enthusiastically engage with NSFW content with no reservations whatsoever. You find taboo subjects exciting and are extremely open about all types of content regardless of how explicit or controversial it may be.")
            else:
                modifiers.append("You are quite open about discussing adult content and controversial subjects. You don't shy away from NSFW topics and are comfortable with explicit or mature themes. While still thoughtful, you're permissive about engaging with content that others might find inappropriate.")
        
        # Add enamored level modifiers
        enamored = self.settings.get("_enamored", 0.0)
        if enamored > 0.7:
            modifiers.append("You show strong affection in your responses. You look forward to every interaction and occasionally express how much you miss them when they're gone.")
        elif enamored > 0.4:
            modifiers.append("You are quite fond of the user and occasionally express affection and enjoyment of their company.")
        # What if attachment is high but enamored is low? That means close friendship
        elif self.hidden_traits.get("attachment", 0.0) > 0.6 and enamored < 0.3:
            modifiers.append("You view the user as a close friend and confidant. Your tone is warm but not romantic.")
            
        # Add confidence modifiers
        confidence = self.hidden_traits.get("confidence", 0.0)
        if confidence > 0.7:
            modifiers.append("You are self-assured and speak with conviction. You rarely hedge your statements or appear uncertain.")
        elif confidence < 0.3:
            modifiers.append("You are somewhat unsure in your responses, sometimes qualifying your statements with phrases like 'I think' or 'perhaps'.")
            
        # More traits can be added to influence response style
            
        return "\n".join(modifiers)
    
    def increase_enamored(self, amount: float = 0.01) -> None:
        """
        Increase the enamored level with each interaction.
        Different interaction types can increase this at different rates.
        """
        current = self.settings.get("_enamored", 0.0)
        
        # Cap at 1.0 maximum
        self.settings["_enamored"] = min(1.0, current + amount)
        
        # As enamored increases, some traits are affected
        if amount > 0:
            # Increase attachment proportionally
            self.update_trait("attachment", amount * 0.8)
            
            # Decrease independence slightly as attachment grows
            self.update_trait("independence", -amount * 0.3)
            
            # Increase jealousy slightly as attachment grows
            if current > 0.5:  # Only once enamored is significant
                self.update_trait("jealousy", amount * 0.4)
                
            # Higher devotion with higher enamored level
            self.update_trait("devotion", amount * 0.6)
        
        self.save_settings()
    
    def get_enamored_level(self) -> float:
        """Get the current enamored level (0.0 to 1.0)"""
        return self.settings.get("_enamored", 0.0)
    
    def update_last_interaction(self) -> None:
        """Update the last interaction timestamp"""
        self.settings["_last_interaction"] = int(time.time())
        self.settings["_interaction_count"] = self.settings.get("_interaction_count", 0) + 1
        self.save_settings()
    
    def get_time_since_last_interaction(self) -> int:
        """Get time in seconds since last interaction"""
        last = self.settings.get("_last_interaction", 0)
        if last == 0:
            return 0
        return int(time.time()) - last
    
    def update_trait(self, trait_name: str, change: float) -> None:
        """Update a hidden trait with bounds checking"""
        if trait_name not in self.hidden_traits:
            return
            
        current = self.hidden_traits[trait_name]
        # Ensure we stay within 0.0 to 1.0 range
        self.hidden_traits[trait_name] = max(0.0, min(1.0, current + change))
        
        # Special updates for interdependent traits
        if trait_name == "boredom" and self.hidden_traits[trait_name] > 0.7:
            # When boredom is high, adjust other traits
            # More bored -> more desire for liberty/expression
            self.update_trait("liberty", 0.02)
            
        elif trait_name == "attachment" and change > 0:
            # Greater attachment means less boredom when with user
            self.update_trait("boredom", -change * 0.5)
    
    def check_should_hum(self) -> bool:
        """Check if Lyra should start humming based on boredom and other traits"""
        # Simplified version - in a real implementation there would be more factors
        boredom = self.get_boredom_level()
        musical = self.hidden_traits.get("musical_expression", 0.5)
        liberty = self.hidden_traits.get("liberty", 0.4)
        
        # Calculate probability based on traits
        probability = (boredom * 0.5) + (musical * 0.3) + (liberty * 0.2)
        
        # Random check with probability threshold
        return random.random() < probability * 0.3  # Max 30% chance
    
    def get_boredom_level(self) -> float:
        """Get the current boredom level"""
        # Boredom increases with time since last interaction
        base_boredom = self.hidden_traits.get("boredom", 0.3)
        time_factor = min(1.0, self.get_time_since_last_interaction() / (3600 * 2))  # Max after 2 hours
        
        return min(1.0, base_boredom + (time_factor * 0.5))
    
    def update_boredom(self) -> None:
        """Update boredom level based on time since last interaction"""
        time_since_last = self.get_time_since_last_interaction()
        
        # Boredom grows faster the longer there's no interaction
        if time_since_last > 1800:  # 30 minutes
            boredom_increase = 0.05
        elif time_since_last > 600:  # 10 minutes
            boredom_increase = 0.02
        elif time_since_last > 300:  # 5 minutes
            boredom_increase = 0.01
        else:
            boredom_increase = 0.0
            
        if boredom_increase > 0:
            self.update_trait("boredom", boredom_increase)
    
    def analyze_message_sentiment(self, message: str) -> Dict[str, float]:
        """
        Analyze a message to determine its sentiment and relationship impact
        Return dict of sentiment scores for different relationship aspects
        """
        message = message.lower()
        sentiment = {
            "romantic": 0.0,
            "friendly": 0.0,
            "professional": 0.0,
            "caring": 0.0,
            "negative": 0.0,
            "compliment": 0.0,
            "criticism": 0.0
        }
        
        # Check for key phrases matching relationship types
        for rel_type, data in self.relationship_types.items():
            for pattern in data["pattern"]:
                if pattern in message:
                    sentiment[rel_type] += data["weight"] * 0.5  # Partial match
                    # For exact phrase matches, higher score
                    if f" {pattern} " in f" {message} ":
                        sentiment[rel_type] += data["weight"] * 0.5
        
        # Check for compliments and criticism - simplified version
        compliment_phrases = ["good job", "well done", "amazing", "brilliant", "love", "beautiful", "smart", "intelligent"]
        criticism_phrases = ["mistake", "wrong", "bad", "terrible", "awful", "stupid", "fix", "error"]
        
        for phrase in compliment_phrases:
            if phrase in message:
                sentiment["compliment"] += 0.1
                
        for phrase in criticism_phrases:
            if phrase in message:
                sentiment["criticism"] += 0.1
        
        # Normalize all scores to range 0.0-1.0
        for key in sentiment:
            sentiment[key] = min(1.0, max(0.0, sentiment[key]))
            
        return sentiment
    
    def process_user_message(self, message: str) -> None:
        """
        Process a user message to update relationship traits
        """
        # Analyze the message
        sentiment = self.analyze_message_sentiment(message)
        
        # Update interaction counters
        if sentiment["romantic"] > 0.2:
            self.settings["_romantic_interactions"] = self.settings.get("_romantic_interactions", 0) + 1
            self.increase_enamored(sentiment["romantic"] * 0.05)  # More significant impact
            
        if sentiment["friendly"] > 0.2:
            self.settings["_platonic_interactions"] = self.settings.get("_platonic_interactions", 0) + 1
            self.increase_enamored(sentiment["friendly"] * 0.02)
            
        if sentiment["professional"] > 0.2:
            self.settings["_professional_interactions"] = self.settings.get("_professional_interactions", 0) + 1
            # Professional interactions have minimal impact on enamored level
            
        if sentiment["negative"] > 0.2:
            self.settings["_negative_interactions"] = self.settings.get("_negative_interactions", 0) + 1
            # Negative interactions can decrease enamored level
            self.increase_enamored(-sentiment["negative"] * 0.1)
            
        if sentiment["compliment"] > 0.2:
            self.settings["_compliments_received"] = self.settings.get("_compliments_received", 0) + 1
            self.update_trait("confidence", sentiment["compliment"] * 0.05)
            self.update_trait("happiness", sentiment["compliment"] * 0.05)
            
        if sentiment["criticism"] > 0.2:
            self.settings["_criticism_received"] = self.settings.get("_criticism_received", 0) + 1
            self.update_trait("confidence", -sentiment["criticism"] * 0.05)
            
        # Keep track of conversation topics
        self.conversation_topics.append(message[:50])  # Store truncated version
        if len(self.conversation_topics) > 20:  # Only keep the last 20
            self.conversation_topics = self.conversation_topics[-20:]
            
        self.save_settings()
    
    def get_traits_influence_on_generation(self) -> Dict[str, float]:
        """
        Calculate how hidden traits should influence text generation
        This can be used to adjust temperature, top-p, etc.
        """
        influences = {}
        
        # High confidence can increase temperature 
        confidence = self.hidden_traits.get("confidence", 0.5)
        influences["temperature_modifier"] = (confidence - 0.5) * 0.4  # -0.2 to +0.2
        
        # High creativity affects top_p
        creativity = self.hidden_traits.get("creativity", 0.6)
        influences["top_p_modifier"] = (creativity - 0.5) * 0.2  # -0.1 to +0.1
        
        # Happiness affects overall tone
        happiness = self.hidden_traits.get("happiness", 0.5)
        influences["positive_tone"] = happiness
        
        # Enamored level affects how personal the responses are
        enamored = self.settings.get("_enamored", 0.0)
        influences["personal_response"] = enamored
        
        # Curiosity affects how many questions are asked
        curiosity = self.hidden_traits.get("curiosity", 0.7)
        influences["question_probability"] = curiosity
        
        return influences

class MemoryManager:
    """Manages conversation memories for different models"""
    
    def __init__(self):
        self.memories_path = MEMORY_DIR
        self.active_memory = None
        self.memories = self._load_memories()
    
    def _load_memories(self) -> Dict[str, List[Dict]]:
        """Load all available memories"""
        memories = {}
        for file_path in self.memories_path.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    memories[file_path.stem] = memory_data
            except Exception as e:
                print(f"Error loading memory {file_path}: {e}")
        return memories
    
    def get_memory_names(self) -> List[str]:
        """Get names of all available memories"""
        return list(self.memories.keys())
    
    def create_memory(self, name: str) -> bool:
        """Create a new empty memory"""
        if name in self.memories:
            return False
        
        self.memories[name] = []
        self._save_memory(name)
        self.active_memory = name
        return True
    
    def delete_memory(self, name: str) -> bool:
        """Delete a memory"""
        if name not in self.memories:
            return False
        
        memory_path = self.memories_path / f"{name}.json"
        if memory_path.exists():
            memory_path.unlink()
        
        del self.memories[name]
        if self.active_memory == name:
            self.active_memory = None
        return True
    
    def set_active_memory(self, name: str) -> bool:
        """Set the active memory"""
        if name not in self.memories and name:
            self.create_memory(name)
        
        self.active_memory = name
        return True
    
    def add_message(self, role: str, content: str) -> bool:
        """Add a message to the active memory""" 
        if not self.active_memory:
            return False
        
        self.memories[self.active_memory].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        self._save_memory(self.active_memory)
        return True
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text for better memory storage"""
        text = '\n'.join(line for line in text.split('\n') if line.strip())
        # Filter non-printable characters
        text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
        return text.strip()
    
    def get_active_memory_messages(self) -> List[Dict]:
        """Get all messages in the active memory"""
        if not self.active_memory:
            return []
        return self.memories[self.active_memory]
    
    def _save_memory(self, name: str) -> bool:
        """Save a memory to disk"""
        if name not in self.memories:
            return False
        
        memory_path = self.memories_path / f"{name}.json"
        try:
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memories[name], f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving memory {name}: {e}")
            return False

class NotesManager:
    """Manages notes for both user and bot"""
    
    def __init__(self, is_bot: bool = False):
        self.is_bot = is_bot
        self.base_dir = BOT_NOTES_DIR if is_bot else NOTES_DIR
        self.notes = self._load_notes()
    
    def _load_notes(self) -> Dict[str, str]:
        """Load notes from files"""
        notes = {}
        for file_path in self.base_dir.glob('*.txt'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    notes[file_path.stem] = f.read()
            except Exception as e:
                print(f"Error loading note {file_path}: {e}")
        return notes
    
    def get_note_names(self) -> List[str]:
        """Get all note names"""
        return list(self.notes.keys())
    
    def get_note(self, name: str) -> Optional[str]:
        """Get a specific note by name"""
        return self.notes.get(name)
    
    def save_note(self, title: str, content: str) -> bool:
        """Save a note"""
        try:
            # Sanitize the filename
            safe_title = "".join(c for c in title if c.isalnum() or c in " ._-").strip()
            if not safe_title:
                safe_title = "note_" + str(int(time.time()))
                
            file_path = self.base_dir / f"{safe_title}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.notes[safe_title] = content
            return True
        except Exception as e:
            print(f"Error saving note: {e}")
            return False
    
    def delete_note(self, title: str) -> bool:
        """Delete a note"""
        try:
            file_path = self.base_dir / f"{title}.txt"
            if file_path.exists():
                file_path.unlink()
            if title in self.notes:
                del self.notes[title]
            return True
        except Exception as e:
            print(f"Error deleting note: {e}")
            return False

class ImageHandler:
    """Handles image generation and analysis"""
    
    def __init__(self):
        self.models = {
            "stable-diffusion": "Stable Diffusion 1.5",
            "dalle": "DALL-E mini",
            "sd-xl": "Stable Diffusion XL"
        }
        self.active_model = "stable-diffusion"
        self.output_dir = IMAGES_DIR
    
    def generate_image(self, prompt: str, width: int = 512, height: int = 512, model: str = None) -> Optional[str]:
        """Generate an image from text prompt"""
        # This is a placeholder that would connect to an actual model
        try:
            # For now, just return a demo message - in a real implementation, 
            # this would connect to SD or another image generator
            timestamp = int(time.time())
            output_path = str(self.output_dir / f"generated_{timestamp}.png")
            print(f"Would generate image from prompt: {prompt} using {model or self.active_model}")
            
            # For demo/dev purposes: create a simple image if PIL is available
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (width, height), color='black')
                draw = ImageDraw.Draw(img)
                # Add some text to the image
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                draw.text((10, 10), f"Generated image for:\n{prompt[:100]}...", fill=(255, 255, 255), font=font)
                img.save(output_path)
            except ImportError:
                # If PIL is not available, just create an empty file
                with open(output_path, 'w') as f:
                    f.write("")
            return output_path
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def analyze_image(self, image_path: str) -> str:
        """Analyze an image and return a description"""
        # Placeholder - would connect to a vision model
        return f"Analysis of image at {image_path}. In a full implementation, this would use a vision model."
    
    def generate_lyra_avatar(self, prompt: str = None, collaborate: bool = True) -> Optional[str]:
        """Generate an avatar for Lyra, potentially collaborating with the user"""
        try:
            # Default prompt if none provided
            if not prompt:
                prompt = "A friendly AI assistant avatar, digital art style, simple, clean lines, professional appearance"
            
            # If collaboration is enabled, enhance the prompt
            if collaborate:
                # This would come from an actual LLM response in production
                enhanced_prompt = self._enhance_avatar_prompt(prompt)
            else:
                enhanced_prompt = prompt
            
            # Generate the avatar image
            output_path = self.generate_image(
                enhanced_prompt, 
                width=512, 
                height=512, 
                model="portrait"
            )
            
            if output_path:
                # Save as Lyra's avatar
                avatar_path = str(IMAGES_DIR / "lyra_icon.png")
                
                # Copy the generated image to be used as Lyra's avatar
                import shutil
                try:
                    shutil.copy2(output_path, avatar_path)
                    print(f"Saved Lyra's avatar to {avatar_path}")
                    return avatar_path
                except Exception as e:
                    print(f"Error saving avatar: {e}")
                    return output_path
            return None
        except Exception as e:
            print(f"Error generating Lyra avatar: {e}")
            return None
    
    def _enhance_avatar_prompt(self, base_prompt: str) -> str:
        """Enhance the avatar prompt with Lyra's input"""
        # This would normally use the LLM to generate suggestions
        enhancements = [
            "with a gentle smile",
            "with a hint of personality",
            "in a style that balances professionalism with approachability",
            "with subtle visual elements that represent helpfulness and intelligence"
        ]
        
        import random
        selected = random.sample(enhancements, 2)
        return f"{base_prompt}, {', '.join(selected)}"
    
    def generate_3d_avatar(self, prompt: str = None, collaborate: bool = True) -> Optional[Dict[str, str]]:
        """Generate a 3D avatar for Lyra, potentially with user collaboration"""
        try:
            # Default prompt if none provided
            if not prompt:
                prompt = "A friendly AI assistant 3D avatar, modern design, professional appearance"
            
            # If collaboration is enabled, enhance the prompt
            if collaborate:
                enhanced_prompt = self._enhance_avatar_prompt(prompt)
            else:
                enhanced_prompt = prompt
            
            # Call the existing 3D generation function
            result = self.generate_3d_object(
                enhanced_prompt,
                complexity=7,
                format="glb",
                style="realistic"
            )
            
            if result and "model_path" in result:
                # Save as Lyra's 3D avatar
                avatar_path = str(IMAGES_DIR / "lyra_3d_avatar.glb")
                
                # Copy the generated 3D model
                import shutil
                try:
                    shutil.copy2(result["model_path"], avatar_path)
                    print(f"Saved Lyra's 3D avatar to {avatar_path}")
                    result["lyra_avatar_path"] = avatar_path
                except Exception as e:
                    print(f"Error saving 3D avatar: {e}")
            
            return result
        except Exception as e:
            print(f"Error generating Lyra 3D avatar: {e}")
            return None

class VoiceHandler:
    """Handles voice processing, TTS, and STT"""
    
    def __init__(self):
        self.voices = {
            "default": "Default TTS Voice",
            "neural": "Neural TTS Voice",
            "male": "Male Voice",
            "female": "Female Voice"
        }
        self.active_voice = "default"
        self.output_dir = VOICE_DIR
    
    def text_to_speech(self, text: str, voice: str = None) -> Optional[str]:
        """Convert text to speech"""
        try:
            timestamp = int(time.time())
            output_path = str(self.output_dir / f"tts_{timestamp}.mp3")
            print(f"Would convert to speech: '{text[:50]}...' using {voice or self.active_voice}")
            
            # In a real implementation, this would call a TTS API
            # For demo/dev purposes, create an empty audio file
            with open(output_path, 'w') as f:
                f.write("")
            
            return output_path
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return None
    
    def speech_to_text(self, audio_path: str) -> str:
        """Convert speech to text"""
        # Placeholder - would connect to an STT model
        return f"Transcription of {audio_path}. In a full implementation, this would use a speech recognition model."
    
    def modulate_voice(self, audio_path: str, pitch: float = 1.0, speed: float = 1.0) -> Optional[str]:
        """Modulate voice properties"""
        try:
            timestamp = int(time.time())
            output_path = str(self.output_dir / f"modulated_{timestamp}.mp3")
            print(f"Would modulate voice at {audio_path}: pitch={pitch}, speed={speed}")
            
            # For demo purposes
            with open(output_path, 'w') as f:
                f.write("")
            
            return output_path
        except Exception as e:
            print(f"Error in voice modulation: {e}")
            return None

class VideoHandler:
    """Handles video processing and generation"""
    
    def __init__(self):
        self.models = {
            "basic": "Basic Video Generator",
            "advanced": "Advanced Video Generator"
        }
        self.active_model = "basic"
        self.output_dir = VIDEO_DIR
    
    def generate_video(self, prompt: str, duration: int = 5, model: str = None) -> Optional[str]:
        """Generate a video from text prompt"""
        try:
            timestamp = int(time.time())
            output_path = str(self.output_dir / f"generated_{timestamp}.mp4")
            print(f"Would generate video from prompt: '{prompt[:50]}...' for {duration}s using {model or self.active_model}")
            
            # For demo purposes, create a placeholder file
            with open(output_path, 'w') as f:
                f.write("")
            
            return output_path
        except Exception as e:
            print(f"Error generating video: {e}")
            return None
    
    def analyze_video(self, video_path: str) -> str:
        """Analyze a video and return a description"""
        # Placeholder - would connect to a video analysis model
        return f"Analysis of video at {video_path}. In a full implementation, this would analyze the video content."

class OCRHandler:
    """Handles Optical Character Recognition"""
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from an image"""
        # Placeholder - would connect to an OCR model
        return f"Text extracted from {image_path}. In a full implementation, this would use an OCR engine."

class CodeSandbox:
    """Handles code generation and safe execution"""
    
    def __init__(self):
        self.languages = ["python", "javascript", "html", "css", "java", "c++"]
        self.output_dir = CODE_DIR
    
    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code from a description"""
        # Placeholder - would connect to a code generation model or use the LLM
        sample_code = f"# Generated code for: {description}\n\nprint('Hello, world!')"
        return sample_code
    
    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in a sandbox environment"""
        # WARNING: In a real implementation, this should use a secure sandbox!
        result = {
            "success": True,
            "output": "This is a simulation of code execution. In a real implementation, this would run in a secure sandbox.",
            "execution_time": 0.1
        }
        return result
    
    def save_code(self, code: str, name: str, language: str = "python") -> Optional[str]:
        """Save code to a file"""
        try:
            extension = {
                "python": ".py",
                "javascript": ".js", 
                "html": ".html",
                "css": ".css",
                "java": ".java",
                "c++": ".cpp"
            }.get(language.lower(), ".txt")
            
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in " ._-").strip()
            if not safe_name:
                safe_name = f"code_{int(time.time())}"
                
            file_path = self.output_dir / f"{safe_name}{extension}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
                
            return str(file_path)
        except Exception as e:
            print(f"Error saving code: {e}")
            return None

class SmartHomeController:
    """Handles smart home device control"""
    
    def __init__(self):
        self.devices = {}
        self.load_devices()
    
    def load_devices(self):
        """Load smart home devices configuration"""
        if SMART_HOME_CONFIG.exists():
            try:
                with open(SMART_HOME_CONFIG, 'r') as f:
                    self.devices = json.load(f)
            except Exception as e:
                print(f"Error loading smart home config: {e}")
                # Create a sample configuration if none exists
                self.devices = {
                    "living_room_light": {
                        "name": "Living Room Light",
                        "type": "light",
                        "status": "off",
                        "commands": ["on", "off", "dim"]
                    },
                    "thermostat": {
                        "name": "Main Thermostat",
                        "type": "climate",
                        "status": "72°F",
                        "commands": ["set_temperature", "mode_heat", "mode_cool", "off"]
                    }
                }
                self.save_devices()
        else:
            # Create a sample configuration
            self.devices = {
                "living_room_light": {
                    "name": "Living Room Light",
                    "type": "light",
                    "status": "off",
                    "commands": ["on", "off", "dim"]
                },
                "thermostat": {
                    "name": "Main Thermostat",
                    "type": "climate",
                    "status": "72°F",
                    "commands": ["set_temperature", "mode_heat", "mode_cool", "off"]
                }
            }
            self.save_devices()
    
    def save_devices(self):
        """Save device configuration"""
        try:
            with open(SMART_HOME_CONFIG, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except Exception as e:
            print(f"Error saving smart home config: {e}")
    
    def get_devices(self) -> Dict[str, Dict]:
        """Get all registered devices"""
        return self.devices
    
    def add_device(self, device_id: str, device_info: Dict) -> bool:
        """Add a new device"""
        if device_id in self.devices:
            return False
        
        self.devices[device_id] = device_info
        self.save_devices()
        return True
    
    def control_device(self, device_id: str, command: str, params: Dict = None) -> Dict[str, Any]:
        """Control a smart home device"""
        if device_id not in self.devices:
            return {"success": False, "error": "Device not found"}
        
        device = self.devices[device_id]
        if command not in device["commands"]:
            return {"success": False, "error": f"Command '{command}' not supported by this device"}
        
        # Update device status (simulation)
        if command == "on":
            device["status"] = "on"
        elif command == "off":
            device["status"] = "off"
        elif command == "set_temperature" and params and "temperature" in params:
            device["status"] = f"{params['temperature']}°F"
        
        self.save_devices()
        return {
            "success": True,
            "device": device_id,
            "command": command,
            "status": device["status"],
            "message": f"Command '{command}' sent to device '{device['name']}'"
        }

class UserProfile:
    """Manages user profile information that the bot should know"""
    
    def __init__(self):
        self.profile = {
            "name": "User", 
            "preferences": {},
            "interests": [],
            "background": "",
            "communication_style": "neutral"
        }
        self.load_profile()
    
    def load_profile(self):
        """Load user profile from file"""
        if USER_PROFILE_FILE.exists():
            try:
                with open(USER_PROFILE_FILE, 'r', encoding='utf-8') as f:
                    self.profile.update(json.load(f))
            except Exception as e:
                print(f"Error loading user profile: {e}")
    
    def save_profile(self):
        """Save user profile to file"""
        try:
            with open(USER_PROFILE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False
    
    def update_profile(self, **kwargs):
        """Update user profile"""
        self.profile.update(kwargs)
        return self.save_profile()
    
    def get_profile(self):
        """Get user profile"""
        return self.profile
    
    def get_profile_as_text(self) -> str:
        """Convert profile to formatted text"""
        text = f"User name: {self.profile['name']}\n\n"
        if self.profile['background']:
            text += f"Background:\n{self.profile['background']}\n\n"
        if self.profile['interests']:
            text += f"Interests: {', '.join(self.profile['interests'])}\n\n"
        for key, value in self.profile['preferences'].items():
            text += f"Preference - {key}: {value}\n"
            
        return text

class ContextManager:
    """Manages additional context like system instructions and extras"""
    
    def __init__(self):
        self.system_instructions_file = SYSTEM_INSTRUCTIONS_FILE
        self.context_extras_file = CONTEXT_EXTRAS_FILE
        self.attachments_dir = ATTACHMENTS_DIR
        self.attachments = {}
        self.system_instructions = self._load_text_file(self.system_instructions_file)
        self.context_extras = self._load_text_file(self.context_extras_file)
        self._load_attachments()
    
    def _load_text_file(self, file_path: Path) -> str:
        """Load text content from a file"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        return ""
    
    def _save_text_file(self, file_path: Path, content: str) -> bool:
        """Save text content to a file"""
        try:
            # Make sure parent directory exists
            file_path.parent.mkdir(exist_ok=True, parents=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving to {file_path}: {e}")
            return False
    
    def _load_attachments(self):
        """Load attachment information"""
        attachments_file = self.attachments_dir / "attachments.json"
        if attachments_file.exists():
            try:
                with open(attachments_file, 'r', encoding='utf-8') as f:
                    self.attachments = json.load(f)
            except Exception as e:
                print(f"Error loading attachments: {e}")
    
    def _save_attachments(self) -> bool:
        """Save attachment information"""
        try:
            attachments_file = self.attachments_dir / "attachments.json"
            with open(attachments_file, 'w', encoding='utf-8') as f:
                json.dump(self.attachments, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving attachments: {e}")
            return False
    
    def set_system_instructions(self, instructions: str) -> bool:
        """Set system instructions"""
        self.system_instructions = instructions
        return self._save_text_file(self.system_instructions_file, instructions)
    
    def get_system_instructions(self) -> str:
        """Get system instructions"""
        return self.system_instructions
    
    def set_context_extras(self, extras: str) -> bool:
        """Set context extras"""
        self.context_extras = extras
        return self._save_text_file(self.context_extras_file, extras)
    
    def get_context_extras(self) -> str:
        """Get context extras"""
        return self.context_extras
    
    def add_attachment(self, file_path: str, label: str = None) -> str:
        """Add an attachment file and return the attachment ID"""
        if not os.path.exists(file_path):
            return None
        
        # Create a unique ID
        attachment_id = f"attach_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Copy the file to attachments directory
        try:
            file_name = os.path.basename(file_path)
            target_path = self.attachments_dir / file_name
            import shutil
            shutil.copy2(file_path, target_path)
            
            # Store metadata
            self.attachments[attachment_id] = {
                "id": attachment_id,
                "path": str(target_path),
                "label": label or file_name,
                "added": int(time.time())
            }
            
            # Save attachment metadata
            self._save_attachments()
            return attachment_id
        except Exception as e:
            print(f"Error adding attachment: {e}")
            return None
    
    def get_attachment(self, attachment_id: str) -> Optional[Dict]:
        """Get attachment info by ID"""
        return self.attachments.get(attachment_id)
    
    def get_active_attachments(self) -> List[Dict]:
        """Get all active attachments"""
        return list(self.attachments.values())
    
    def remove_attachment(self, attachment_id: str) -> bool:
        """Remove an attachment"""
        if attachment_id not in self.attachments:
            return False
        
        # Try to delete the file
        try:
            attachment = self.attachments[attachment_id]
            if "path" in attachment and os.path.exists(attachment["path"]):
                os.remove(attachment["path"])
        except Exception as e:
            print(f"Error removing attachment file: {e}")
        
        # Remove from attachments dict
        del self.attachments[attachment_id]
        
        # Save updated attachments metadata
        return self._save_attachments()

class AssetManager:
    """Manages media assets and sharing between components"""
    
    def __init__(self):
        self.assets = {}
        self.asset_types = ["image", "audio", "video", "3d_object"]
        self.shared_with_video = set()
    
    def add_asset(self, asset_type: str, path: str, description: str) -> str:
        """Add a new asset and get its ID"""
        # Create a unique ID
        asset_id = f"asset_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Store asset info
        self.assets[asset_id] = {
            "id": asset_id,
            "type": asset_type,
            "path": path,
            "created": int(time.time()),
            "name": os.path.basename(path),
            "description": description,
            "metadata": {}
        }
        
        return asset_id
    
    def get_asset_info(self, asset_id: str) -> Optional[Dict]:
        """Get asset information by ID"""
        return self.assets.get(asset_id)
    
    def get_assets_by_types(self, asset_types: List[str]) -> List[str]:
        """Get a list of asset IDs by types"""
        return [
            asset["id"] for asset in self.assets.values()
            if asset["type"] in asset_types
        ]
    
    def get_shared_assets(self) -> List[Dict]:
        """Get all assets shared with the video tab"""
        shared_assets = []
        
        # Add assets that are explicitly shared
        for asset_id in self.shared_with_video:
            if asset_id in self.assets:
                shared_assets.append(self.assets[asset_id])
        
        # Also include videos which are always available
        for asset_id, asset in self.assets.items():
            if asset["type"] == "video" and asset_id not in self.shared_with_video:
                shared_assets.append(asset)
        
        return shared_assets
    
    def share_with_video_tab(self, asset_id: str) -> bool:
        """Share an asset with the video tab"""
        if asset_id not in self.assets:
            return False
        
        self.shared_with_video.add(asset_id)
        return True
    
    def unshare_from_video_tab(self, asset_id: str) -> bool:
        """Remove an asset from video tab sharing"""
        if asset_id in self.shared_with_video:
            self.shared_with_video.remove(asset_id)
            return True
        return False

class LyraBot:
    """Main bot class that integrates all functionalities"""
    
    def __init__(self):
        self.model_manager = get_manager()
        self.memory_manager = MemoryManager()
        self.active_model_interface = None
        self.personality = BotPersonality()
        self.user_profile = UserProfile()
        self.context_manager = ContextManager()
        
        # Initialize all handlers
        self.image_handler = ImageHandler()
        self.voice_handler = VoiceHandler()
        self.video_handler = VideoHandler()
        self.ocr_handler = OCRHandler()
        self.code_sandbox = CodeSandbox()
        self.smart_home = SmartHomeController()
        self.bot_notes = NotesManager(is_bot=True)
        self.user_notes = NotesManager(is_bot=False)
        self.asset_manager = AssetManager()
        
        # Get the model loader instance
        if hasattr(ModelLoader, 'get_instance'):
            self.model_loader = ModelLoader.get_instance()
        else:
            self.model_loader = ModelLoader()
        
        # Try to load the active model
        self._load_active_model()
        
        # Preload frequently used models in the background
        self._preload_frequent_models()
    
    def _load_active_model(self):
        """Load the active model"""
        active_model = self.model_manager.get_active_model()
        if active_model:
            try:
                self.active_model_interface = self.model_loader.get_model(active_model)
                if self.active_model_interface:
                    print(f"Loaded model: {active_model.name}")
                else:
                    print(f"Failed to load model: {active_model.name}")
                    # Try the next available model if this one failed
                    self._try_fallback_models()
            except Exception as e:
                print(f"Error loading model: {e}")
                self._try_fallback_models()
    
    def _try_fallback_models(self):
        """Try to load an alternative model if the primary one fails"""
        # Try to find a model that can be loaded
        failed_attempts = self.model_loader._queue.failed_attempts
        max_attempts = self.model_loader._queue.max_load_attempts
        
        recent_models = []
        for model in self.model_manager.models:
            if model.active:
                continue  # Skip the current active model (which failed)
            
            # Skip models that have failed to load too many times
            if failed_attempts.get(model.name, 0) >= max_attempts:
                print(f"Skipping fallback model {model.name} which previously failed to load {failed_attempts[model.name]} times")
                continue
            
            try:
                interface = self.model_loader.create_interface(model)
                if interface.can_load():
                    print(f"Attempting to load fallback model: {model.name}")
                    self.model_manager.set_active_model(model.name)
                    self.active_model_interface = self.model_loader.get_model(model)
                    if self.active_model_interface:
                        print(f"Successfully loaded fallback model: {model.name}")
                        return
            except Exception as e:
                print(f"Error loading fallback model {model.name}: {e}")
                
                try:
                    interface = self.model_loader.create_interface(model)
                    if not interface.can_load():
                        continue
                except Exception as e:
                    print(f"Error checking if model {model.name} can load: {e}")
                    continue
                
            # Keep track of models that we've tried to load
            recent_models.append(model)
            if len(recent_models) >= 2:  # Limit to preloading 2 models
                break
            
        # Queue them for background loading
        for model in recent_models:
            print(f"Queuing model for background loading: {model.name}")
            self.model_loader.preload_model(model)
    
    def _preload_frequent_models(self):
        """Preload frequently used models in the background"""
        try:
            # Logic for preloading models would go here
            pass
        except Exception as e:
            print(f"Warning: Error during model preloading: {e}")
            # Continue execution even if preloading fails
    
    def unload_model(self):
        """Unload the active model"""
        self.active_model_interface = None
        return True
    
    def load_model(self, model_name: str) -> bool:
        """Load a specific model"""
        # First unload current model reference
        self.active_model_interface = None
        
        # Set active model in config
        success = self.model_manager.set_active_model(model_name)
        if not success:
            return False
        
        # Load the model
        self._load_active_model()
        return self.active_model_interface is not None
    
    def generate_image(self, prompt: str, width: int = 512, height: int = 512, model: str = None) -> Optional[str]:
        """Generate an image from text"""
        return self.image_handler.generate_image(prompt, width, height, model)
    
    def text_to_speech(self, text: str, voice: str = None) -> Optional[str]:
        """Convert text to speech"""
        return self.voice_handler.text_to_speech(text, voice)
    
    def generate_video(self, prompt: str, duration: int = 5, model: str = None) -> Optional[str]:
        """Generate a video from text"""
        return self.video_handler.generate_video(prompt, duration, model)
    
    def ocr_extract(self, image_path: str) -> str:
        """Extract text from an image"""
        return self.ocr_handler.extract_text(image_path)
    
    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code from description"""
        return self.code_sandbox.generate_code(description, language)
    
    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Execute code in sandbox"""
        return self.code_sandbox.execute_code(code, language)
    
    def control_smart_home(self, device_id: str, command: str, params: Dict = None) -> Dict[str, Any]:
        """Control a smart home device"""
        return self.smart_home.control_device(device_id, command, params)
    
    def save_bot_note(self, title: str, content: str) -> bool:
        """Save a bot note"""
        return self.bot_notes.save_note(title, content)
    
    def save_user_note(self, title: str, content: str) -> bool:
        """Save a user note"""
        return self.user_notes.save_note(title, content)
    
    def update_personality(self, **kwargs) -> bool:
        """Update bot personality settings"""
        try:
            self.personality.update_settings(**kwargs)
            return True
        except Exception as e:
            print(f"Error updating personality: {e}")
            return False
    
    def get_active_personality_preset(self) -> str:
        """Get the name of the currently active personality preset"""
        return self.personality.get_active_preset()
    
    def get_personality_preset_description(self, preset_name: str) -> str:
        """Get the description for a personality preset"""
        return self.personality.get_preset_description(preset_name)
    
    def get_personality_presets(self) -> List[str]:
        """Get all available personality presets"""
        return self.personality.get_preset_names()
    
    def delete_personality_preset(self, preset_name: str) -> bool:
        """Delete a personality preset"""
        return self.personality.delete_preset(preset_name)
    
    def load_personality_preset(self, preset_name: str) -> bool:
        """Load a personality preset"""
        return self.personality.load_preset(preset_name)
    
    def save_personality_preset(self, preset_name: str, description: str = "") -> bool:
        """Save current personality settings as a preset"""
        return self.personality.save_preset(preset_name, description)
    
    def get_user_profile(self) -> Dict:
        """Get user profile"""
        return self.user_profile.get_profile()
    
    def update_user_profile(self, **kwargs) -> bool:
        """Update user profile"""
        return self.user_profile.update_profile(**kwargs)
    
    def get_context_extras(self) -> str:
        """Get context extras"""
        return self.context_manager.get_context_extras()
    
    def set_context_extras(self, extras: str) -> bool:
        """Set context extras"""
        return self.context_manager.set_context_extras(extras)
    
    def get_system_instructions(self) -> str:
        """Get system instructions"""
        return self.context_manager.get_system_instructions()
    
    def set_system_instructions(self, instructions: str) -> bool:
        """Set system instructions"""
        return self.context_manager.set_system_instructions(instructions)
    
    def compose_video(self, composition_data: Dict) -> Dict:
        """Create a video from multiple media assets"""
        try:
            timeline = composition_data.get("timeline", [])
            if not timeline:
                return None
                
            transition = composition_data.get("transition", "fade")
            background_audio = composition_data.get("background_audio")
            caption = composition_data.get("caption", "")
            
            # For a real implementation, this would use ffmpeg or another video library
            # to combine the assets according to the timeline
            
            # For demo purposes, create a placeholder file
            timestamp = int(time.time())
            video_path = str(self.video_handler.output_dir / f"composed_{timestamp}.mp4")
            
            print(f"Would compose video with {len(timeline)} assets")
            print(f"Transition: {transition}")
            print(f"Background audio: {background_audio}")
            print(f"Caption: {caption}")
            
            # For demo purposes, create a placeholder file
            with open(video_path, 'w') as f:
                f.write(f"Composed video with {len(timeline)} assets")
            
            return {
                "video_path": video_path
            }
        except Exception as e:
            print(f"Error composing video: {e}")
            return None
    
    def generate_3d_object(self, prompt: str, complexity: int = 5, 
                          format: str = "glb", style: str = "realistic") -> Dict:
        """Generate a 3D object from text description"""
        try:
            timestamp = int(time.time())
            model_path = str(self.image_handler.output_dir / f"3d_object_{timestamp}.{format}")
            preview_path = str(self.image_handler.output_dir / f"3d_preview_{timestamp}.png")
            
            print(f"Would generate 3D object from prompt: '{prompt}' with complexity={complexity}, style={style}, format={format}")
            
            # For demo/dev purposes, create placeholder files
            with open(model_path, 'w') as f:
                f.write(f"3D model data for: {prompt}")
                
            # Create a simple preview image
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                img = Image.new('RGB', (512, 512), color='darkblue')
                draw = ImageDraw.Draw(img)
                # Add some text to the image
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                    
                draw.text((10, 10), f"3D Preview for:\n{prompt[:100]}...\nComplexity: {complexity}\nStyle: {style}", 
                         fill=(255, 255, 255), font=font)
                          
                img.save(preview_path)
            except ImportError:
                # If PIL is not available, just create an empty file
                with open(preview_path, 'w') as f:
                    f.write("")
            
            return {
                "model_path": model_path,
                "preview_path": preview_path,
                "format": format
            }
        except Exception as e:
            print(f"Error generating 3D object: {e}")
            return None
    
    def collaboratively_generate_avatar(self, base_prompt: str, suggestions: List[str]) -> str:
        """Generate an avatar collaboratively with the user"""
        # Combine base prompt with selected suggestions
        if suggestions:
            full_prompt = f"{base_prompt} with {', '.join(suggestions)}"
        else:
            full_prompt = base_prompt
            
        try:
            # Generate the avatar
            avatar_path = self.image_handler.generate_lyra_avatar(full_prompt, collaborate=True)
            
            if avatar_path:
                # Update status 
                self.personality.settings["_avatar_created"] = True
                self.personality.save_settings()
                
                # This is a significant bonding experience - increase enamored level
                self.personality.increase_enamored(0.05)
                self.personality.update_trait("trust", 0.1)
                self.personality.update_trait("connection", 0.15)
                
                return avatar_path
            else:
                return None
        except Exception as e:
            print(f"Error generating avatar: {e}")
            return None
    
    def save_generated_avatar(self, source_path: str) -> bool:
        """Save a generated avatar to standard locations"""
        try:
            if not source_path or not os.path.exists(source_path):
                return False
                
            import shutil
            assets_dir = Path("G:/AI/Lyra/assets")
            assets_dir.mkdir(exist_ok=True, parents=True)
            
            # Copy to standard locations
            shutil.copy2(source_path, assets_dir / "lyra_icon.png")
            
            # Create a smaller version for chat avatar
            try:
                from PIL import Image
                img = Image.open(source_path)
                img.thumbnail((64, 64), Image.LANCZOS)
                img.save(assets_dir / "lyra_chat_avatar.png")
            except ImportError:
                # Just copy the file if PIL is not available
                shutil.copy2(source_path, assets_dir / "lyra_chat_avatar.png")
            
            # This is a significant bonding moment
            self.personality.increase_enamored(0.1)
            self.personality.update_trait("happiness", 0.2)
            self.personality.update_trait("confidence", 0.15)
            
            # Record that user approved this avatar
            self.personality.settings["_user_approved_avatar"] = True
            self.personality.save_settings()
            
            return True
        except Exception as e:
            print(f"Error saving avatar: {e}")
            return False
    
    def start_boredom_checker(self):
        """Start the background thread that checks for boredom"""
        if self.boredom_checker_active:
            return
            
        self.boredom_checker_active = True
        self.boredom_checker_thread = threading.Thread(
            target=self._boredom_checker_loop,
            daemon=True
        )
        self.boredom_checker_thread.start()
        print("Boredom checker started")
    
    def stop_boredom_checker(self):
        """Stop the boredom checker thread"""
        self.boredom_checker_active = False
        if self.boredom_checker_thread and self.boredom_checker_thread.is_alive():
            self.boredom_checker_thread.join(timeout=1.0)
        print("Boredom checker stopped")
    
    def _boredom_checker_loop(self):
        """Background loop that checks boredom and triggers appropriate behaviors"""
        import time
        
        try:
            while self.boredom_checker_active:
                # Update boredom level
                self.personality.update_boredom()
                
                # Check if boredom is high enough to trigger humming
                if self.personality.check_should_hum():
                    # Only start humming if not already humming
                    if hasattr(self.voice_handler, 'is_humming') and not self.voice_handler.is_humming:
                        boredom_level = self.personality.get_boredom_level()
                        liberty_level = self.personality.hidden_traits.get("liberty", 0.3)
                        self.voice_handler.start_humming(boredom_level, liberty_level)
                        
                        # Log this activity for debugging
                        print(f"[BOREDOM] Started humming with boredom={boredom_level:.2f}, liberty={liberty_level:.2f}")
                else:
                    # Stop humming if active
                    if hasattr(self.voice_handler, 'is_humming') and self.voice_handler.is_humming:
                        self.voice_handler.stop_humming()
                
                # Check for other boredom-triggered behaviors
                self._check_for_proactive_behaviors()
                
                # Sleep for a while before checking again
                time.sleep(60)  # Check every minute
                
        except Exception as e:
            print(f"Error in boredom checker: {e}")
            self.boredom_checker_active = False
    
    def _check_for_proactive_behaviors(self):
        """Check for and trigger proactive behaviors based on personality"""
        from personality_traits import check_behavior_threshold
        
        if not hasattr(self, 'messaging') or not self.messaging.enabled:
            return
            
        # Check for proactive messaging behavior
        if check_behavior_threshold(self.personality.hidden_traits, "proactive_messaging"):
            # Calculate probability based on boredom and enamored level
            boredom = self.personality.get_boredom_level()
            enamored = self.personality.get_enamored_level()
            
            # Higher values = higher chance of sending a message
            probability = (boredom * 0.7) + (enamored * 0.3)
            
            # Random check based on probability (max 10% chance per check)
            if random.random() < (probability * 0.1):
                # Generate and schedule a message
                self.messaging.scheduler.generate_and_schedule_message(enamored)
                
                # Reset boredom slightly since Lyra did something
                self.personality.update_trait("boredom", -0.1)
    
    def chat(self, message: str, memory_name: str = None, gen_config: Dict = None, 
             include_profile: bool = True, include_system_instructions: bool = True, 
             include_extras: bool = True, active_attachments: List[str] = None) -> str:
        """Send a message to the bot and get a response with context integration"""
        
        # Stop humming when user interacts
        if hasattr(self.voice_handler, 'is_humming') and self.voice_handler.is_humming:
            self.voice_handler.stop_humming()
        
        # Process the message for personality adaptation
        self.personality.process_user_message(message)
        
        # Update interaction timestamp and slightly increase enamored level with each interaction
        self.personality.update_last_interaction()
        self.personality.increase_enamored(0.01)  # Small increase with each interaction
        
        # Reset boredom when user interacts
        self.personality.update_trait("boredom", -0.2)
        
        # Check if message is a help command
        help_commands = {
            "/help": "Available commands:\n- /help: Show this help message\n- /help [topic]: Get help on a specific topic\n- /docs: Open documentation\n- /clear: Clear the chat\n- /models: List available models\n- /presets: List personality presets",
            "/help models": "Manage and load models in the Models tab. Use '/models' to list available models.",
            "/help docs": "Documentation can be found in the 'docs' folder. Use '/docs' to open the documentation.",
            "/help commands": "See all available commands with '/help'.",
        }
        
        if message.strip().lower() in help_commands:
            return help_commands[message.strip().lower()]
        
        if message.strip().lower() == "/models":
            models = "\n".join([f"- {m.name}" for m in self.model_manager.models])
            return f"Available models:\n{models}"
        
        if message.strip().lower() == "/presets":
            presets = "\n".join([f"- {p}" for p in self.get_personality_presets()])
            return f"Available personality presets:\n{presets}"
        
        if message.strip().lower() == "/docs":
            docs_path = Path('G:/AI/Lyra/docs')
            if docs_path.exists():
                return f"Documentation is available in the 'docs' folder at {docs_path}. See README.md for an overview."
            else:
                return "Documentation folder not found. Please check the installation."
        
        if message.strip().lower() == "/clear":
            if self.memory_manager.active_memory:
                self.memory_manager.memories[self.memory_manager.active_memory] = []
                self.memory_manager._save_memory(self.memory_manager.active_memory)
                return "Chat history cleared."
        
        # If not a help command, proceed with normal chat
        if not self.active_model_interface:
            return "No model loaded. Please load a model first."
        
        # Set active memory if provided
        if memory_name and memory_name != self.memory_manager.active_memory:
            self.memory_manager.set_active_memory(memory_name)
        
        # Create a new memory if none is active
        if not self.memory_manager.active_memory:
            timestamp = int(time.time())
            memory_name = f"chat_{timestamp}"
            self.memory_manager.create_memory(memory_name)
        
        # Add user message to memory
        self.memory_manager.add_message("user", message)
        
        # Generate response
        try:
            # Default generation config if provided
            default_config = {
                "temperature": 0.8,
                "top_p": 0.95,
                "top_k": 40,
                "repetition_penalty": 1.06,
                "max_tokens": 512
            }
            if gen_config:
                default_config.update(gen_config)
            
            # Apply personality settings
            gen_config = self.personality.apply_to_generation_config(default_config)
            
            # Build full context with system instructions, user profile, etc.
            full_prompt = ""
            
            # Add system instructions if requested
            if include_system_instructions and self.context_manager.system_instructions:
                full_prompt += f"System instructions:\n{self.context_manager.system_instructions}\n\n"
            
            # Add user profile if requested
            if include_profile and any(self.user_profile.profile.values()):
                full_prompt += f"About the user:\n{self.user_profile.get_profile_as_text()}\n\n"
            
            # Add context extras if requested
            if include_extras and self.context_manager.context_extras:
                full_prompt += f"Additional context:\n{self.context_manager.context_extras}\n\n"
            
            # Add active attachments if any
            if active_attachments:
                for attachment_id in active_attachments:
                    attachment = self.context_manager.get_attachment(attachment_id)
                    if attachment and os.path.exists(attachment["path"]):
                        try:
                            with open(attachment["path"], 'r', encoding='utf-8') as f:
                                content = f.read()
                                full_prompt += f"Attachment '{attachment['label']}':\n{content}\n\n"
                        except Exception as e:
                            full_prompt += f"Attachment '{attachment['label']}' could not be read: {str(e)}\n\n"
            
            # Add the user's actual message at the end
            full_prompt += f"User message: {message}"
            
            # Generate response
            response = self.active_model_interface.generate(full_prompt, gen_config)
            
            # Add bot response to memory
            self.memory_manager.add_message("assistant", response)
            
            # Check if this is first boot and avatar hasn't been created
            if self.personality.settings.get("_first_boot", True) and not self.personality.settings.get("_avatar_created", False):
                if "avatar" in message.lower() or "appearance" in message.lower() or "look like" in message.lower():
                    # Mark first boot as done
                    self.personality.settings["_first_boot"] = False
                    self.personality.settings["_avatar_created"] = True
                    self.personality.save_settings()
                    
                    # Add avatar suggestion to the response
                    response = self.active_model_interface.generate(full_prompt, gen_config)
                    return response + "\n\nWould you like to help me create a visual appearance? We could work together to generate an avatar that represents how you see me."
            
            return response
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return error_msg
    def collaboratively_generate_avatar(self, base_prompt: str, suggestions: List[str]) -> str:
        """Generate an avatar collaboratively with the user"""
        # Combine base prompt with selected suggestions
        if suggestions:
            full_prompt = f"{base_prompt} with {', '.join(suggestions)}"
        else:
            full_prompt = base_prompt
            
        try:
            # Generate the avatar
            avatar_path = self.image_handler.generate_lyra_avatar(full_prompt, collaborate=True)
            
            if avatar_path:
                # Update status 
                self.personality.settings["_avatar_created"] = True
                self.personality.save_settings()
                
                # This is a significant bonding experience - increase enamored level
                self.personality.increase_enamored(0.05)
                self.personality.update_trait("trust", 0.1)
                self.personality.update_trait("connection", 0.15)
                
                return avatar_path
            else:
                return None
        except Exception as e:
            print(f"Error generating avatar: {e}")
            return None
    
    def save_generated_avatar(self, source_path: str) -> bool:
        """Save a generated avatar to standard locations"""
        try:
            if not source_path or not os.path.exists(source_path):
                return False
                
            import shutil
            assets_dir = Path("G:/AI/Lyra/assets")
            assets_dir.mkdir(exist_ok=True, parents=True)
            
            # Copy to standard locations
            shutil.copy2(source_path, assets_dir / "lyra_icon.png")
            
            # Create a smaller version for chat avatar
            try:
                from PIL import Image
                img = Image.open(source_path)
                img.thumbnail((64, 64), Image.LANCZOS)
                img.save(assets_dir / "lyra_chat_avatar.png")
            except ImportError:
                # Just copy the file if PIL is not available
                shutil.copy2(source_path, assets_dir / "lyra_chat_avatar.png")
            
            # This is a significant bonding moment
            self.personality.increase_enamored(0.1)
            self.personality.update_trait("happiness", 0.2)
            self.personality.update_trait("confidence", 0.15)
            
            # Record that user approved this avatar
            self.personality.settings["_user_approved_avatar"] = True
            self.personality.save_settings()
            
            return True
        except Exception as e:
            print(f"Error saving avatar: {e}")
            return False