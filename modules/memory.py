# ...existing code...

def add_message(self, message, max_tokens=None):
    try:
        if max_tokens is None:
            max_tokens = self.max_tokens if hasattr(self, 'max_tokens') and self.max_tokens else 8192
            
        # Calculate token count of the message
        token_count = count_tokens(message.content) if message else 0
        
        # Don't add empty messages
        if not message or not message.content.strip():
            return True
            
        self.messages.append(message)
        self.update_token_count()
        
        # Trim messages if necessary
        while self.token_count > max_tokens and len(self.messages) > 1:
            # Keep the system message if it exists
            start_idx = 1 if self.messages[0].role == "system" else 0
            if len(self.messages) > start_idx:
                self.messages.pop(start_idx)
                self.update_token_count()
            else:
                break
                
        return True
    except Exception as e:
        logger.error(f"Error adding message to memory: {str(e)}")
        return False
        
# ...existing code...
