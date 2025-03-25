import json
import logging
from fastapi import FastAPI, HTTPException, Body, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from modules.register_improvement import register_collaborative_improvement, is_available
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("improvement_api")

# Setup the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Replaces the deprecated on_event handlers with the recommended lifespan approach.
    """
    # Startup code that was previously in on_event("startup")
    print("Starting Improvement API server...")
    # Initialize any resources needed
    global components
    if not is_available():
        raise Exception("Collaborative improvement requirements not available")
    
    components = register_collaborative_improvement()
    if not components:
        raise Exception("Failed to register collaborative improvement module")
    
    logger.info("API server initialized with collaborative improvement components")
    
    yield  # This is where the app runs
    
    # Shutdown code that was previously in on_event("shutdown")
    print("Shutting down Improvement API server...")
    # Clean up resources

app = FastAPI(
    title="Collaborative Improvement API",
    description="API for interacting with the Lyra Collaborative Improvement module",
    version="0.1.0",
    lifespan=lifespan
)

# Data models
class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class MediaGenerationRequest(BaseModel):
    prompt: str
    media_type: str  # "image", "video", or "3d"
    params: Optional[Dict[str, Any]] = None

class CodeImprovementRequest(BaseModel):
    module: str
    description: str
    code_example: str
    estimated_impact: float

# Global component storage
components = None

@app.get("/")
async def root():
    return {"status": "Collaborative Improvement API is running"}

@app.post("/message")
async def process_message(request: MessageRequest):
    global components
    if not components:
        raise HTTPException(status_code=500, detail="Components not initialized")
    
    try:
        processor = components["processor"]
        result = processor.process_user_input(request.message)
        return {
            "response": result["response"],
            "topics": result["learning_results"]["main_themes"],
            "sentiment": result["learning_results"]["sentiment_score"],
            "cycle": result["cycle_number"]
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-media")
async def generate_media(request: MediaGenerationRequest):
    global components
    if not components:
        raise HTTPException(status_code=500, detail="Components not initialized")
    
    try:
        media_integrator = components["media_integrator"]
        result = media_integrator.generate_media({
            "type": request.media_type,
            "prompt": request.prompt,
            "params": request.params or {},
            "detected": True
        })
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Media generation failed"))
        
        return {
            "id": result["id"],
            "path": result["path"],
            "media_type": result["type"]
        }
    except Exception as e:
        logger.error(f"Error generating media: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest-improvement")
async def suggest_improvement(request: CodeImprovementRequest):
    global components
    if not components:
        raise HTTPException(status_code=500, detail="Components not initialized")
    
    try:
        from modules.code_updater import CodeUpdater
        code_updater = CodeUpdater()
        
        suggestion = {
            "module": request.module,
            "description": request.description,
            "code_example": request.code_example,
            "estimated_impact": request.estimated_impact
        }
        
        suggestion_id = code_updater.save_suggestion(suggestion)
        if not suggestion_id:
            raise HTTPException(status_code=500, detail="Failed to save suggestion")
        
        return {
            "suggestion_id": suggestion_id,
            "status": "pending"
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="Code updater not available")
    except Exception as e:
        logger.error(f"Error suggesting improvement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api(host="0.0.0.0", port=8000):
    """Start the API server"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api()
