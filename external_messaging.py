"""
External messaging module for Lyra that handles sending messages to the user's devices
"""
import time
import threading
import random
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import os

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lyra_messaging")

# Message scheduler constants
CHECK_INTERVAL = 300  # Check for scheduled messages every 5 minutes
MIN_TIME_BETWEEN_MESSAGES = 3600  # Minimum 1 hour between messages by default
MAX_STORED_MESSAGES = 100  # Maximum number of messages to keep in history

class MessageScheduler:
    """Handles scheduling and sending messages based on enamored level"""
    
    def __init__(self, lyra_bot=None):
        self.lyra_bot = lyra_bot
        self.running = False
        self.scheduler_thread = None
        self.messages_file = Path('G:/AI/Lyra/data/scheduled_messages.json')
        self.messages_dir = self.messages_file.parent
        self.messages_dir.mkdir(exist_ok=True, parents=True)
        
        # Queue of scheduled messages
        self.message_queue = []
        self.message_history = []
        
        # Load existing messages
        self.load_messages()
    
    def start(self):
        """Start the message scheduler"""
        if self.running:
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Message scheduler started")
    
    def stop(self):
        """Stop the message scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        logger.info("Message scheduler stopped")
    
    def load_messages(self):
        """Load scheduled messages from file"""
        if self.messages_file.exists():
            try:
                with open(self.messages_file, 'r') as f:
                    data = json.load(f)
                    self.message_queue = data.get('queue', [])
                    self.message_history = data.get('history', [])
                logger.info(f"Loaded {len(self.message_queue)} scheduled messages")
            except Exception as e:
                logger.error(f"Error loading messages: {e}")
                self.message_queue = []
                self.message_history = []
    
    def save_messages(self):
        """Save scheduled messages to file"""
        try:
            with open(self.messages_file, 'w') as f:
                json.dump({
                    'queue': self.message_queue,
                    'history': self.message_history[-MAX_STORED_MESSAGES:]  # Keep only the most recent
                }, f, indent=2)
            logger.info(f"Saved {len(self.message_queue)} scheduled messages")
        except Exception as e:
            logger.error(f"Error saving messages: {e}")
    
    def schedule_message(self, content: str, timestamp: Optional[int] = None, 
                        platforms: List[str] = None, importance: int = 1):
        """Schedule a message to be sent"""
        if timestamp is None:
            # Schedule for a random time in the next few hours
            delay = random.randint(MIN_TIME_BETWEEN_MESSAGES, MIN_TIME_BETWEEN_MESSAGES * 3)
            timestamp = int(time.time()) + delay
        
        if platforms is None:
            platforms = ["telegram", "sms"]
            
        message = {
            'content': content,
            'timestamp': timestamp,
            'platforms': platforms,
            'importance': importance,
            'id': f"msg_{int(time.time())}_{random.randint(1000, 9999)}"
        }
        
        self.message_queue.append(message)
        self.message_queue.sort(key=lambda x: x['timestamp'])  # Sort by timestamp
        self.save_messages()
        logger.info(f"Scheduled message: {content[:30]}... for {timestamp}")
        return message['id']
    
    def generate_and_schedule_message(self, enamored_level: float):
        """Generate a message based on enamored level and schedule it"""
        if not self.lyra_bot:
            logger.warning("Cannot generate message: LyraBot not set")
            return
        
        # Adjust frequency based on enamored level
        if enamored_level < 0.2:
            # Very infrequent messages
            if random.random() > 0.2:  # Only 20% chance to even schedule
                return
            delay = random.randint(24*3600, 72*3600)  # 1-3 days
            importance = 1
        elif enamored_level < 0.5:
            # Occasional messages
            if random.random() > 0.5:  # 50% chance to schedule
                return
            delay = random.randint(12*3600, 36*3600)  # 12-36 hours
            importance = 2
        elif enamored_level < 0.8:
            # Regular messages
            delay = random.randint(4*3600, 12*3600)  # 4-12 hours
            importance = 3
        else:
            # Frequent messages
            delay = random.randint(1*3600, 6*3600)  # 1-6 hours
            importance = 4
        
        # Generate message content
        topics = [
            "Thinking about our last conversation",
            "Had an interesting thought to share",
            "Wondering what you're up to",
            "Found something you might like",
            "Missing our chats",
            "Just wanted to check in"
        ]
        
        prompts = [
            f"You are Lyra, an AI assistant with an enamored level of {enamored_level:.2f} (0.0-1.0). "
            f"Create a short, casual message to send to your user about: {random.choice(topics)}. "
            f"Keep it under 100 characters and appropriate to your attachment level."
        ]
        
        try:
            # Use the bot to generate a message
            response = self.lyra_bot.active_model_interface.generate(prompts[0], {
                "temperature": 0.7,
                "max_tokens": 100
            })
            
            # Schedule the message
            timestamp = int(time.time()) + delay
            
            # Determine platforms based on importance
            platforms = ["notification"]
            if importance >= 2:
                platforms.append("telegram")
            if importance >= 4:
                platforms.append("sms")
                
            self.schedule_message(response, timestamp, platforms, importance)
            
        except Exception as e:
            logger.error(f"Error generating message: {e}")
    
    def _scheduler_loop(self):
        """Main scheduler loop that checks for messages to send"""
        while self.running:
            try:
                now = int(time.time())
                
                # Check for messages to send
                messages_to_send = [msg for msg in self.message_queue if msg['timestamp'] <= now]
                
                # Remove sent messages from queue
                if messages_to_send:
                    self.message_queue = [msg for msg in self.message_queue if msg['timestamp'] > now]
                    
                    # Send each message
                    for message in messages_to_send:
                        self._send_message(message)
                        
                        # Add to history
                        message['sent_at'] = now
                        self.message_history.append(message)
                    
                    # Save updated queue and history
                    self.save_messages()
                
                # If we have a bot reference, check if we should generate new messages
                if self.lyra_bot and random.random() < 0.2:  # 20% chance each check interval
                    enamored_level = self.lyra_bot.personality.get_enamored_level()
                    time_since_last = self.lyra_bot.personality.get_time_since_last_interaction()
                    
                    # Only generate new messages if it's been a while since last interaction
                    if time_since_last > MIN_TIME_BETWEEN_MESSAGES:
                        self.generate_and_schedule_message(enamored_level)
                
                # Sleep before next check
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(CHECK_INTERVAL)  # Sleep and retry
    
    def _send_message(self, message: Dict[str, Any]):
        """Actually send the message to configured platforms"""
        content = message.get('content', '')
        platforms = message.get('platforms', [])
        
        logger.info(f"Sending message: {content[:30]}... to {platforms}")
        
        # Send to each platform
        for platform in platforms:
            try:
                if platform == "telegram":
                    self._send_telegram(content)
                elif platform == "sms":
                    self._send_sms(content)
                elif platform == "notification":
                    self._send_notification(content)
            except Exception as e:
                logger.error(f"Error sending to {platform}: {e}")
    
    def _send_telegram(self, content: str):
        """Send message via Telegram"""
        # This would integrate with the Telegram API
        # For example purposes, just log it
        logger.info(f"[TELEGRAM] {content}")
        
        # In a real implementation, you would use the Telegram Bot API
        # Example:
        # import telegram
        # bot = telegram.Bot(token=TELEGRAM_TOKEN)
        # bot.send_message(chat_id=CHAT_ID, text=content)
    
    def _send_sms(self, content: str):
        """Send message via SMS"""
        # This would integrate with an SMS API like Twilio
        logger.info(f"[SMS] {content}")
        
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(TWILIO_SID, TWILIO_TOKEN)
        # client.messages.create(
        #     body=content,
        #     from_=TWILIO_PHONE,
        #     to=USER_PHONE
        # )
    
    def _send_notification(self, content: str):
        """Send as a desktop notification"""
        logger.info(f"[NOTIFICATION] {content}")
        
        # On Windows:
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast("Lyra", content, duration=10)
        except:
            # Fallback or other platforms
            try:
                # For Linux/Mac
                os.system(f'notify-send "Lyra" "{content}"')
            except:
                pass

class MessageIntegration:
    """Primary interface for message integration with the Lyra assistant"""
    
    def __init__(self, lyra_bot=None):
        self.scheduler = MessageScheduler(lyra_bot)
        self.enabled = False
        self.config_file = Path('G:/AI/Lyra/config/messaging.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load messaging configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading messaging config: {e}")
        
        # Default config
        return {
            "enabled": False,
            "platforms": {
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_id": ""
                },
                "sms": {
                    "enabled": False,
                    "provider": "twilio",
                    "account_sid": "",
                    "auth_token": "",
                    "from_number": "",
                    "to_number": ""
                },
                "notification": {
                    "enabled": True
                }
            },
            "frequency": {
                "min_time_between_messages": 3600,  # 1 hour
                "max_messages_per_day": 5
            }
        }
    
    def _save_config(self):
        """Save messaging configuration"""
        self.config_file.parent.mkdir(exist_ok=True, parents=True)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving messaging config: {e}")
    
    def start(self):
        """Start the messaging integration"""
        if self.config.get("enabled", False):
            self.enabled = True
            self.scheduler.start()
            logger.info("Message integration started")
    
    def stop(self):
        """Stop the messaging integration"""
        self.enabled = False
        self.scheduler.stop()
        logger.info("Message integration stopped")
    
    def update_config(self, config: Dict):
        """Update messaging configuration"""
        self.config.update(config)
        self._save_config()
        
        # Apply changes if needed
        if self.enabled and not self.config.get("enabled", False):
            self.stop()
        elif not self.enabled and self.config.get("enabled", False):
            self.start()
    
    def schedule_message(self, content: str, delay: int = None):
        """Schedule a message to be sent after the specified delay"""
        if not self.enabled:
            logger.warning("Cannot schedule message: messaging is disabled")
            return
        
        if delay is None:
            # Default delay based on config
            min_time = self.config.get("frequency", {}).get("min_time_between_messages", 3600)
            delay = random.randint(min_time, min_time * 2)
        
        timestamp = int(time.time()) + delay
        
        # Determine which platforms to use based on config
        platforms = []
        for platform, settings in self.config.get("platforms", {}).items():
            if settings.get("enabled", False):
                platforms.append(platform)
        
        if not platforms:
            platforms = ["notification"]  # Default fallback
        
        return self.scheduler.schedule_message(content, timestamp, platforms)
