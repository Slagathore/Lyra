import os
import logging
import time
import threading
import requests
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent
        self.config_path = os.path.join(base_dir, "data", "telegram_config.json")
        self.api_token = None
        self.enabled = False
        self.notification_thread = None
        self.should_run = False
        self.queue = []
        self.queue_lock = threading.Lock()
        self.max_queue_size = 100
        self.last_error = None
        self.last_success_time = None
        
        # Load config
        self.load_config()
        
    def load_config(self):
        """Load Telegram configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_token = config.get("api_token", None)
                    self.enabled = config.get("enabled", False)
                    logger.info("Loaded Telegram configuration")
                    
                    # Validate the token immediately
                    if self.api_token:
                        self._validate_token()
        except Exception as e:
            logger.error(f"Error loading Telegram configuration: {str(e)}")
            self.last_error = str(e)
            
    def save_config(self):
        """Save Telegram configuration"""
        try:
            config = {
                "api_token": self.api_token,
                "enabled": self.enabled
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            logger.info("Saved Telegram configuration")
            return True
        except Exception as e:
            logger.error(f"Error saving Telegram configuration: {str(e)}")
            self.last_error = str(e)
            return False
            
    def _validate_token(self) -> bool:
        """Validate the Telegram bot token"""
        try:
            url = f"https://api.telegram.org/bot{self.api_token}/getMe"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    logger.info(f"Successfully validated Telegram bot: {data['result']['username']}")
                    return True
            logger.error("Invalid Telegram bot token")
            self.last_error = "Invalid bot token"
            return False
        except Exception as e:
            logger.error(f"Error validating Telegram token: {str(e)}")
            self.last_error = str(e)
            return False
            
    def set_api_token(self, token: str) -> bool:
        """Set the Telegram API token"""
        if not token:
            self.last_error = "Empty token provided"
            return False
            
        # Validate the token before saving
        self.api_token = token
        if self._validate_token():
            self.save_config()
            return True
        
        self.api_token = None
        return False
        
    def enable(self, state: bool = True) -> bool:
        """Enable or disable Telegram notifications"""
        if state and not self.api_token:
            logger.warning("Cannot enable Telegram notifications without an API token")
            self.last_error = "No API token configured"
            return False
            
        if state and not self._validate_token():
            logger.error("Cannot enable Telegram notifications - token validation failed")
            return False
            
        self.enabled = state
        self.save_config()
        
        if state and not self.is_running():
            self.start_notification_thread()
        elif not state and self.is_running():
            self.stop_notification_thread()
            
        return self.enabled
        
    def is_running(self) -> bool:
        """Check if the notification thread is running"""
        return self.notification_thread is not None and self.notification_thread.is_alive()
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Telegram notifier"""
        return {
            "enabled": self.enabled,
            "running": self.is_running(),
            "has_token": bool(self.api_token),
            "queue_size": len(self.queue),
            "last_error": self.last_error,
            "last_success": self.last_success_time
        }
        
    def start_notification_thread(self) -> bool:
        """Start the notification thread"""
        if self.is_running():
            return True
            
        try:
            self.should_run = True
            self.notification_thread = threading.Thread(
                target=self._process_notifications,
                daemon=True
            )
            self.notification_thread.start()
            logger.info("Started Telegram notification thread")
            return True
        except Exception as e:
            logger.error(f"Error starting notification thread: {str(e)}")
            self.last_error = str(e)
            return False
            
    def stop_notification_thread(self) -> bool:
        """Stop the notification thread"""
        if not self.is_running():
            return True
            
        try:
            self.should_run = False
            self.notification_thread.join(timeout=5.0)
            self.notification_thread = None
            logger.info("Stopped Telegram notification thread")
            return True
        except Exception as e:
            logger.error(f"Error stopping notification thread: {str(e)}")
            self.last_error = str(e)
            return False
            
    def send_message(self, username: str, message: str, priority: int = 0) -> bool:
        """Queue a message to be sent to a Telegram user"""
        if not self.enabled:
            logger.warning("Telegram notifications are disabled")
            return False
            
        if not username or not message:
            logger.warning("Username and message are required")
            return False
            
        try:
            with self.queue_lock:
                if len(self.queue) >= self.max_queue_size:
                    logger.warning("Telegram message queue is full")
                    return False
                    
                self.queue.append({
                    "username": username.lstrip('@'),
                    "message": message,
                    "priority": priority,
                    "timestamp": time.time()
                })
            return True
        except Exception as e:
            logger.error(f"Error queueing message: {str(e)}")
            self.last_error = str(e)
            return False
            
    def _process_notifications(self):
        """Background thread to process notification queue"""
        while self.should_run:
            try:
                # Process all queued messages
                with self.queue_lock:
                    if self.queue:
                        msg = self.queue.pop(0)
                        success = self._send_telegram_message(
                            msg["username"],
                            msg["message"]
                        )
                        if success:
                            self.last_success_time = time.time()
                            self.last_error = None
            except Exception as e:
                logger.error(f"Error processing notifications: {str(e)}")
                self.last_error = str(e)
            
            # Sleep briefly to prevent busy-waiting
            time.sleep(0.1)
            
    def _get_chat_id(self, username: str) -> Optional[str]:
        """Get chat_id for a Telegram username"""
        if not username:
            return None
            
        try:
            # Strip @ if present
            username = username.lstrip('@')
            
            # Try to get chat updates to find the user
            url = f"https://api.telegram.org/bot{self.api_token}/getUpdates"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    # Look for messages from this user
                    for update in data["result"]:
                        message = update.get("message", {})
                        from_user = message.get("from", {})
                        if from_user.get("username") == username:
                            return str(message["chat"]["id"])
            return None
        except Exception as e:
            logger.error(f"Error getting chat ID: {str(e)}")
            self.last_error = str(e)
            return None
            
    def _send_telegram_message(self, username: str, message: str) -> bool:
        """Send a message directly to Telegram"""
        try:
            # First we need to get the chat_id for the username
            chat_id = self._get_chat_id(username)
            if not chat_id:
                logger.warning(f"Could not find chat_id for Telegram user {username}")
                return False
            
            # Now send the message
            url = f"https://api.telegram.org/bot{self.api_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Sent Telegram message to {username}")
                return True
            else:
                logger.error(f"Error sending Telegram message: {response.text}")
                self.last_error = response.text
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            self.last_error = str(e)
            return False

# Global instance
_telegram_notifier = None

def get_telegram_notifier():
    """Get the global Telegram notifier instance"""
    global _telegram_notifier
    if (_telegram_notifier is None):
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier
