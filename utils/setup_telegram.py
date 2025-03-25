import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from modules.telegram_notify import TelegramNotifier, get_telegram_notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_telegram():
    """Initialize and start the Telegram notification system"""
    try:
        # Get credentials
        cred_path = r'G:\AI\Lyra\secure_credentials.json'
        if not os.path.exists(cred_path):
            logger.info("No credentials file found")
            return False
            
        with open(cred_path, 'r') as f:
            creds = json.load(f)
            
        token = creds.get('telegram', {}).get('bot_token', '')
        if not token:
            logger.info("No Telegram token found in credentials")
            return False

        # Get or create the notifier
        notifier = get_telegram_notifier()
        
        # Set the token and enable notifications
        if notifier.set_api_token(token):
            notifier.enable(True)
            logger.info("Telegram notifications enabled successfully")
            return True
        else:
            logger.error("Failed to set Telegram API token")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up Telegram: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_telegram()
    exit(0 if success else 1)