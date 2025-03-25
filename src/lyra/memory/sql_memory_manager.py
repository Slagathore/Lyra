import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from typing import List, Dict, Any, Optional

Base = declarative_base()

class Conversation(Base):
    """Conversation model for storing chat history"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_input = Column(Text)
    bot_response = Column(Text)
    conversation_data = Column(Text)  # Renamed from 'metadata' which is a reserved name
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user': self.user_input,
            'bot': self.bot_response,
            'metadata': json.loads(self.conversation_data) if self.conversation_data else {}
        }

# Initialize database connection
DATABASE_URL = os.environ.get("LYRA_DATABASE_URL", "sqlite:///conversation_history.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    """Initialize the database tables"""
    Base.metadata.create_all(engine)

def log_conversation(user_input: str, bot_response: str, tags: List[str] = None, 
                    sentiment: float = 0, entities: List[str] = None):
    """
    Log a conversation turn to the database
    
    Args:
        user_input: User's message
        bot_response: Bot's response
        tags: List of tags/topics for this conversation
        sentiment: Sentiment score (-1 to 1)
        entities: List of entities mentioned
    """
    # Create metadata
    metadata = {
        "tags": tags or [],
        "sentiment": sentiment,
        "entities": entities or [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Create database session
    session = Session()
    
    # Create new conversation record
    conversation = Conversation(
        user_input=user_input,
        bot_response=bot_response,
        conversation_data=json.dumps(metadata)  # Use conversation_data field instead of metadata
    )
    
    # Add and commit
    session.add(conversation)
    session.commit()
    session.close()

def get_recent_conversations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most recent conversation entries
    
    Args:
        limit: Maximum number of entries to return
        
    Returns:
        List of conversation dictionaries
    """
    session = Session()
    conversations = session.query(Conversation).order_by(Conversation.timestamp.desc()).limit(limit).all()
    result = [conv.to_dict() for conv in conversations]
    session.close()
    return result

def search_conversations(query: str) -> List[Dict[str, Any]]:
    """
    Search conversations by content
    
    Args:
        query: Search term
        
    Returns:
        List of matching conversation dictionaries
    """
    session = Session()
    search_term = f"%{query}%"
    conversations = session.query(Conversation).filter(
        (Conversation.user_input.like(search_term)) | 
        (Conversation.bot_response.like(search_term))
    ).all()
    result = [conv.to_dict() for conv in conversations]
    session.close()
    return result

# Ensure tables are created when module is imported
init_db()
