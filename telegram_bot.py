"""
Telegram Bot Integration for Lyra
Allows interaction with Lyra via Telegram
"""

import os
import sys
import time
import json
import logging
import threading
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_bot.log")
    ]
)
logger = logging.getLogger("telegram_bot")

try:
    import telegram
    from telegram import Update, ForceReply
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("Telegram library not available. Install with: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False

class LyraTelegramBot:
    """
    Telegram bot integration for Lyra
    Allows users to interact with Lyra through Telegram
    """
    
    def __init__(self, token: str = None, config_path: str = None, lyra_interface = None):
        self.token = token
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", "telegram_config.json"
        )
        self.lyra_interface = lyra_interface
        self.authorized_users = []
        self.authorized_chats = []
        self.active = False
        self.updater = None
        self.initialized = False
        
        # Load configuration
        self._load_config()
        
        # Check if Telegram is available
        if not TELEGRAM_AVAILABLE:
            logger.error("Cannot initialize Telegram bot - library not available")
            return
        
        # Initialize the bot
        self._initialize_bot()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            # Check if config directory exists
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # Check if config file exists
            if not os.path.exists(self.config_path):
                # Create default config
                default_config = {
                    "token": self.token or "",
                    "authorized_users": [],
                    "authorized_chats": []
                }
                
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    
                logger.info(f"Created default config at {self.config_path}")
                
                # If token is not provided, we can't continue
                if not self.token:
                    logger.warning("No Telegram token provided. Please add your token to the config file.")
                    return
            else:
                # Load existing config
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Use token from config if not provided in init
                if not self.token:
                    self.token = config.get("token", "")
                
                # Load authorized users and chats
                self.authorized_users = config.get("authorized_users", [])
                self.authorized_chats = config.get("authorized_chats", [])
                
                # Still need a token
                if not self.token:
                    logger.warning("No Telegram token found in config. Please add your token.")
                    return
        except Exception as e:
            logger.error(f"Error loading Telegram config: {e}")
    
    def _initialize_bot(self):
        """Initialize the Telegram bot"""
        if not self.token:
            logger.error("Cannot initialize Telegram bot - no token provided")
            return
            
        try:
            # Create the updater and dispatcher
            self.updater = Updater(self.token)
            dispatcher = self.updater.dispatcher
            
            # Add command handlers
            dispatcher.add_handler(CommandHandler("start", self._start_command))
            dispatcher.add_handler(CommandHandler("help", self._help_command))
            dispatcher.add_handler(CommandHandler("auth", self._auth_command))
            dispatcher.add_handler(CommandHandler("status", self._status_command))
            
            # Add message handler for general messages
            dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self._handle_message))
            
            # Log errors
            dispatcher.add_error_handler(self._error_handler)
            
            logger.info("Telegram bot initialized successfully")
            self.initialized = True
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
    
    def _start_command(self, update: Update, context: CallbackContext):
        """Handle the /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check if user is authorized
        if not self._is_authorized(user.id, chat_id):
            update.message.reply_text(
                f"Hello {user.first_name}! I'm Lyra, but I'm not authorized to chat with you yet. "
                f"Please contact my administrator to get access."
            )
            logger.info(f"Unauthorized access attempt from user {user.id} ({user.first_name})")
            return
        
        update.message.reply_text(
            f"Hello {user.first_name}! I'm Lyra, your AI assistant. How can I help you today?"
        )
    
    def _help_command(self, update: Update, context: CallbackContext):
        """Handle the /help command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check if user is authorized
        if not self._is_authorized(user.id, chat_id):
            return
        
        update.message.reply_text(
            "Here's how you can interact with me:\n\n"
            "- Just send me messages and I'll respond\n"
            "- Use /status to check my current status\n"
            "- Use /auth to add a new authorized user (admin only)\n"
            "- Use /help to see this message again"
        )
    
    def _auth_command(self, update: Update, context: CallbackContext):
        """Handle the /auth command to add authorized users"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Only existing authorized users can add new ones
        if not self._is_authorized(user.id, chat_id):
            update.message.reply_text("Sorry, you're not authorized to use this command.")
            return
        
        # Check if user provided an ID to authorize
        if not context.args:
            update.message.reply_text(
                "Please provide a user ID to authorize.\n"
                "Usage: /auth <user_id>"
            )
            return
        
        try:
            # Get the user ID to authorize
            new_user_id = int(context.args[0])
            
            # Add to authorized users if not already there
            if new_user_id not in self.authorized_users:
                self.authorized_users.append(new_user_id)
                self._save_config()
                update.message.reply_text(f"User {new_user_id} has been authorized.")
                logger.info(f"User {user.id} authorized new user {new_user_id}")
            else:
                update.message.reply_text(f"User {new_user_id} is already authorized.")
        except ValueError:
            update.message.reply_text("Invalid user ID. Please provide a valid integer ID.")
    
    def _status_command(self, update: Update, context: CallbackContext):
        """Handle the /status command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Check if user is authorized
        if not self._is_authorized(user.id, chat_id):
            return
        
        # Get Lyra's status if interface is available
        if self.lyra_interface:
            try:
                # Get thinking state
                thinking_state = "Unknown"
                if hasattr(self.lyra_interface, 'get_thinking_state'):
                    thinking = self.lyra_interface.get_thinking_state()
                    if thinking.get("is_thinking"):
                        thinking_state = f"Thinking about: {thinking['active_task']['description']}"
                    else:
                        thinking_state = "Idle"
                
                # Get emotional state if available
                emotional_state = "Unknown"
                if hasattr(self.lyra_interface, 'get_emotional_state'):
                    emotion = self.lyra_interface.get_emotional_state()
                    emotional_state = f"{emotion['dominant_emotion']} ({emotion['intensity']:.2f})"
                
                status_message = (
                    "📊 Lyra Status 📊\n\n"
                    f"🧠 Thinking: {thinking_state}\n"
                    f"😊 Emotional State: {emotional_state}\n"
                    f"👥 Connected Users: {len(self.authorized_users)}\n"
                    f"🔄 Bot Active: {'Yes' if self.active else 'No'}"
                )
                
                update.message.reply_text(status_message)
            except Exception as e:
                logger.error(f"Error getting Lyra status: {e}")
                update.message.reply_text("Error retrieving status information.")
        else:
            # Basic status if no Lyra interface
            update.message.reply_text(
                "📊 Telegram Bot Status 📊\n\n"
                f"👥 Authorized Users: {len(self.authorized_users)}\n"
                f"💬 Authorized Chats: {len(self.authorized_chats)}\n"
                f"🔄 Bot Active: {'Yes' if self.active else 'No'}\n"
                f"🔌 Connected to Lyra: {'No' if self.lyra_interface is None else 'Yes'}"
            )
    
    def _handle_message(self, update: Update, context: CallbackContext):
        """Handle regular text messages"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        message_text = update.message.text
        
        # Check if user is authorized
        if not self._is_authorized(user.id, chat_id):
            return
        
        # Process with Lyra if interface is available
        if self.lyra_interface:
            try:
                # Send typing action while processing
                context.bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
                
                # Process message with Lyra
                response = self._process_with_lyra(message_text, user.id)
                
                # Send response
                update.message.reply_text(response)
                
                # Log the interaction
                logger.info(f"Message from {user.id}: {message_text[:30]}... | Response: {response[:30]}...")
            except Exception as e:
                logger.error(f"Error processing message with Lyra: {e}")
                update.message.reply_text("Sorry, I encountered an error while processing your message.")
        else:
            # No Lyra interface available
            update.message.reply_text(
                "I'm currently disconnected from my thinking systems. "
                "Please try again later or contact my administrator."
            )
    
    def _process_with_lyra(self, message: str, user_id: int) -> str:
        """Process a message with the Lyra interface"""
        if not self.lyra_interface:
            # Try to create a simple fallback processor if there's no interface
            try:
                from modules.fallback_llm import get_instance as get_fallback_llm
                fallback = get_fallback_llm()
                if fallback and fallback.initialized:
                    logger.info("Using fallback LLM for processing")
                    return fallback.generate_text(message)
            except ImportError:
                pass
                
            # Try to use Phi model directly
            try:
                from model_backends.phi_backend import PhiInterface
                phi = PhiInterface("phi-2")
                if phi.initialize():
                    logger.info("Using Phi model for processing")
                    return phi.generate_text(message)
            except ImportError:
                pass
                
            return "I'm currently disconnected from my thinking systems."
        
        # Check for appropriate method to handle messages
        if hasattr(self.lyra_interface, 'chat'):
            return self.lyra_interface.chat(message, user_id=user_id, source="telegram")
        elif hasattr(self.lyra_interface, 'process_message'):
            return self.lyra_interface.process_message(message, user_id=user_id, source="telegram")
        elif hasattr(self.lyra_interface, 'generate_response'):
            return self.lyra_interface.generate_response(message)
        else:
            logger.warning("Lyra interface doesn't have a suitable method to process messages")
            return "I can't process messages right now due to a configuration issue."
    
    def _error_handler(self, update: object, context: CallbackContext):
        """Handle errors in the dispatcher"""
        logger.error(f"Update {update} caused error: {context.error}")
        
        # Try to notify user if possible
        if update and hasattr(update, 'message') and update.message:
            try:
                update.message.reply_text("Sorry, an error occurred while processing your request.")
            except:
                pass
    
    def _is_authorized(self, user_id: int, chat_id: int) -> bool:
        """Check if a user and chat are authorized"""
        # If no authorized users are configured, allow anyone (for initial setup)
        if not self.authorized_users and not self.authorized_chats:
            return True
            
        return (user_id in self.authorized_users) or (chat_id in self.authorized_chats)
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config = {
                "token": self.token,
                "authorized_users": self.authorized_users,
                "authorized_chats": self.authorized_chats
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving Telegram config: {e}")
    
    def start(self):
        """Start the Telegram bot"""
        if not self.initialized:
            logger.error("Cannot start Telegram bot - not initialized")
            return False
            
        try:
            # Start the bot
            self.updater.start_polling()
            logger.info("Telegram bot started")
            self.active = True
            return True
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            return False
    
    def stop(self):
        """Stop the Telegram bot"""
        if not self.active or not self.updater:
            return
            
        try:
            # Stop the bot
            self.updater.stop()
            logger.info("Telegram bot stopped")
            self.active = False
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
    
    def connect_lyra_interface(self, lyra_interface):
        """Connect the Lyra interface for message processing"""
        self.lyra_interface = lyra_interface
        logger.info("Connected Lyra interface to Telegram bot")

def create_bot(token: str = None, lyra_interface = None) -> Optional[LyraTelegramBot]:
    """Create and start a Telegram bot"""
    if not TELEGRAM_AVAILABLE:
        logger.error("Telegram library not available - cannot create bot")
        return None
        
    # Check for environment variable if token not provided
    if not token:
        token = os.environ.get("LYRA_TELEGRAM_TOKEN")
        
    # Still no token? Try loading from config
    if not token:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config", "telegram_config.json"
        )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    token = config.get("token")
            except:
                pass
    
    # Create and start the bot
    bot = LyraTelegramBot(token=token, lyra_interface=lyra_interface)
    
    if bot.initialized:
        if bot.start():
            return bot
    
    return None

def main():
    """Run the Telegram bot as a standalone application"""
    parser = argparse.ArgumentParser(description="Lyra Telegram Bot")
    parser.add_argument("--token", type=str, help="Telegram bot token")
    args = parser.parse_args()
    
    # Create and start the bot
    bot = create_bot(token=args.token)
    
    if not bot:
        logger.error("Failed to create Telegram bot")
        return
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Telegram bot")
        bot.stop()

if __name__ == "__main__":
    main()
