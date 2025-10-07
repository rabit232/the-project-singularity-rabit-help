#!/usr/bin/env python3
"""
Project Singularity API Server
FastAPI backend for the Text-to-APK engine with real-time WebSocket support
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our core engine
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.text_to_apk_engine import TextToAPKEngine, AppFramework, AppCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Project Singularity API",
    description="Revolutionary Text-to-APK Engine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Text-to-APK engine
engine = TextToAPKEngine(openai_api_key=os.getenv("OPENAI_API_KEY"))

# In-memory storage for demo (use Redis/PostgreSQL in production)
active_generations = {}
generation_history = {}

class GenerationRequest(BaseModel):
    """Request model for APK generation"""
    prompt: str = Field(..., description="Natural language description of the desired app")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for framework, style, etc.")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    
class GenerationResponse(BaseModel):
    """Response model for APK generation"""
    generation_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None

class GenerationStatus(BaseModel):
    """Status model for generation progress"""
    generation_id: str
    status: str
    progress: int  # 0-100
    current_stage: str
    estimated_remaining: Optional[int] = None
    error: Optional[str] = None

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, generation_id: str):
        await websocket.accept()
        self.active_connections[generation_id] = websocket
        logger.info(f"WebSocket connected for generation {generation_id}")
    
    def disconnect(self, generation_id: str):
        if generation_id in self.active_connections:
            del self.active_connections[generation_id]
            logger.info(f"WebSocket disconnected for generation {generation_id}")
    
    async def send_update(self, generation_id: str, data: Dict[str, Any]):
        if generation_id in self.active_connections:
            try:
                await self.active_connections[generation_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send WebSocket update: {e}")
                self.disconnect(generation_id)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Project Singularity: Text-to-APK Engine API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "generate": "/generate",
            "status": "/status/{generation_id}",
            "download": "/download/{generation_id}",
            "websocket": "/ws/{generation_id}",
            "docs": "/docs"
        }
    }

@app.post("/generate", response_model=GenerationResponse)
async def generate_apk(request: GenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate APK from natural language prompt
    """
    try:
        # Generate unique ID for this generation
        generation_id = str(uuid.uuid4())
        
        # Validate request
        if not request.prompt or len(request.prompt.strip()) < 10:
            raise HTTPException(status_code=400, detail="Prompt must be at least 10 characters long")
        
        # Initialize generation tracking
        active_generations[generation_id] = {
            "id": generation_id,
            "prompt": request.prompt,
            "user_preferences": request.user_preferences,
            "user_id": request.user_id,
            "status": "queued",
            "progress": 0,
            "current_stage": "Initializing",
            "created_at": datetime.utcnow(),
            "estimated_time": 180  # 3 minutes default
        }
        
        # Start background generation task
        background_tasks.add_task(process_generation, generation_id, request)
        
        logger.info(f"Started APK generation {generation_id} for prompt: {request.prompt[:100]}...")
        
        return GenerationResponse(
            generation_id=generation_id,
            status="queued",
            message="APK generation started successfully",
            estimated_time=180
        )
        
    except Exception as e:
        logger.error(f"Failed to start APK generation: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/status/{generation_id}", response_model=GenerationStatus)
async def get_generation_status(generation_id: str):
    """
    Get the current status of an APK generation
    """
    if generation_id not in active_generations and generation_id not in generation_history:
        raise HTTPException(status_code=404, detail="Generation not found")
    
    # Check active generations first
    if generation_id in active_generations:
        gen_data = active_generations[generation_id]
        return GenerationStatus(
            generation_id=generation_id,
            status=gen_data["status"],
            progress=gen_data["progress"],
            current_stage=gen_data["current_stage"],
            estimated_remaining=gen_data.get("estimated_remaining"),
            error=gen_data.get("error")
        )
    
    # Check completed generations
    if generation_id in generation_history:
        gen_data = generation_history[generation_id]
        return GenerationStatus(
            generation_id=generation_id,
            status=gen_data["status"],
            progress=100 if gen_data["status"] == "completed" else 0,
            current_stage="Completed" if gen_data["status"] == "completed" else "Failed",
            error=gen_data.get("error")
        )

@app.get("/download/{generation_id}")
async def download_apk(generation_id: str):
    """
    Download the generated APK file
    """
    if generation_id not in generation_history:
        raise HTTPException(status_code=404, detail="Generation not found or not completed")
    
    gen_data = generation_history[generation_id]
    
    if gen_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="APK generation not completed")
    
    if "apk_path" not in gen_data or not os.path.exists(gen_data["apk_path"]):
        raise HTTPException(status_code=404, detail="APK file not found")
    
    return FileResponse(
        path=gen_data["apk_path"],
        filename=f"{gen_data['app_name']}.apk",
        media_type="application/vnd.android.package-archive"
    )

@app.websocket("/ws/{generation_id}")
async def websocket_endpoint(websocket: WebSocket, generation_id: str):
    """
    WebSocket endpoint for real-time generation updates
    """
    await websocket_manager.connect(websocket, generation_id)
    
    try:
        # Send initial status if generation exists
        if generation_id in active_generations:
            gen_data = active_generations[generation_id]
            await websocket_manager.send_update(generation_id, {
                "type": "status_update",
                "status": gen_data["status"],
                "progress": gen_data["progress"],
                "current_stage": gen_data["current_stage"]
            })
        
        # Keep connection alive
        while True:
            try:
                # Wait for any message (ping/pong)
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(generation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(generation_id)

@app.get("/history")
async def get_generation_history(limit: int = 10, user_id: Optional[str] = None):
    """
    Get generation history (optionally filtered by user)
    """
    history = list(generation_history.values())
    
    if user_id:
        history = [gen for gen in history if gen.get("user_id") == user_id]
    
    # Sort by creation time (newest first)
    history.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return {
        "generations": history[:limit],
        "total": len(history)
    }

@app.get("/frameworks")
async def get_supported_frameworks():
    """
    Get list of supported development frameworks
    """
    return {
        "frameworks": [
            {
                "id": framework.value,
                "name": framework.value.replace("_", " ").title(),
                "description": f"{framework.value.replace('_', ' ').title()} development framework"
            }
            for framework in AppFramework
        ]
    }

@app.get("/categories")
async def get_app_categories():
    """
    Get list of supported app categories
    """
    return {
        "categories": [
            {
                "id": category.value,
                "name": category.value.title(),
                "description": f"{category.value.title()} applications"
            }
            for category in AppCategory
        ]
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_generations": len(active_generations),
        "completed_generations": len(generation_history),
        "engine_status": "operational"
    }

async def process_generation(generation_id: str, request: GenerationRequest):
    """
    Background task to process APK generation
    """
    try:
        logger.info(f"Processing generation {generation_id}")
        
        # Update status to processing
        await update_generation_status(generation_id, "processing", 10, "Analyzing prompt")
        
        # Simulate processing stages with real engine calls
        stages = [
            ("analyzing", 20, "Analyzing prompt and extracting requirements"),
            ("architecting", 40, "Generating application architecture"),
            ("coding", 70, "Generating source code"),
            ("building", 90, "Building APK file"),
            ("finalizing", 95, "Finalizing and optimizing")
        ]
        
        for stage, progress, description in stages:
            await update_generation_status(generation_id, "processing", progress, description)
            await asyncio.sleep(2)  # Simulate processing time
        
        # Call the actual engine
        result = await engine.generate_apk_from_text(
            request.prompt, 
            request.user_preferences
        )
        
        if result["success"]:
            # Move to completed
            gen_data = active_generations[generation_id]
            gen_data.update({
                "status": "completed",
                "progress": 100,
                "current_stage": "Completed",
                "completed_at": datetime.utcnow(),
                "apk_path": result["apk_path"],
                "app_name": result["app_specification"]["name"],
                "framework": result["app_specification"]["framework"],
                "build_time": result["metadata"]["generation_time"]
            })
            
            # Move to history
            generation_history[generation_id] = gen_data
            del active_generations[generation_id]
            
            await websocket_manager.send_update(generation_id, {
                "type": "completed",
                "status": "completed",
                "progress": 100,
                "download_url": f"/download/{generation_id}",
                "app_name": result["app_specification"]["name"]
            })
            
            logger.info(f"Generation {generation_id} completed successfully")
            
        else:
            # Handle failure
            await update_generation_status(
                generation_id, 
                "failed", 
                0, 
                "Generation failed", 
                result.get("error", "Unknown error")
            )
            
            logger.error(f"Generation {generation_id} failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Generation {generation_id} failed with exception: {e}")
        await update_generation_status(
            generation_id, 
            "failed", 
            0, 
            "Generation failed", 
            str(e)
        )

async def update_generation_status(generation_id: str, status: str, progress: int, stage: str, error: Optional[str] = None):
    """
    Update generation status and notify WebSocket clients
    """
    if generation_id in active_generations:
        gen_data = active_generations[generation_id]
        gen_data.update({
            "status": status,
            "progress": progress,
            "current_stage": stage,
            "updated_at": datetime.utcnow()
        })
        
        if error:
            gen_data["error"] = error
        
        # Send WebSocket update
        await websocket_manager.send_update(generation_id, {
            "type": "status_update",
            "status": status,
            "progress": progress,
            "current_stage": stage,
            "error": error
        })

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
