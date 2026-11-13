import os
import json
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.vector_db import LightweightVectorDB
from backend.agent import AnalysisUnavailable, DigitalTwinAgent, sessions

logger = logging.getLogger(__name__)

# API Key and Model configuration — set OPENROUTER_API_KEY as env variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = "nvidia/nemotron-3-ultra-550b-a55b:free"

# Initialize FastAPI app
app = FastAPI(title="Ayush Tiwari Portfolio AI Backend")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector database and agent
db = LightweightVectorDB(api_key=OPENROUTER_API_KEY)
# Pre-build vector index (reads cache or builds it)
try:
    db.build_index()
except Exception as e:
    print(f"Error during initialization of vector index: {e}")

agent = DigitalTwinAgent(api_key=OPENROUTER_API_KEY, db=db, model=MODEL_NAME)

# Pydantic models for request bodies
class ChatRequest(BaseModel):
    session_id: str
    message: str

class CompatibilityRequest(BaseModel):
    job_description: str

class ResetRequest(BaseModel):
    session_id: str

@app.get("/api/resume")
async def get_resume():
    """Returns the full structured resume JSON."""
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_data.json")
    if not os.path.exists(data_path):
        raise HTTPException(status_code=404, detail="Resume data store file not found")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/config")
async def get_config():
    """Returns application configuration parameters like primary model name."""
    return {"model": MODEL_NAME}

@app.post("/api/chat")
def post_chat(payload: ChatRequest):
    """Chat endpoint for interacting with the AI twin."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    try:
        reply = agent.chat(payload.session_id, payload.message)
        return {"reply": reply}
    except Exception as e:
        logger.exception("Request processing failed")
        raise HTTPException(status_code=500, detail="Request processing failed") from e

@app.post("/api/analyze-compatibility")
def post_analyze_compatibility(payload: CompatibilityRequest):
    """Endpoint for analyzing fit with a pasted job description."""
    if not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    try:
        analysis = agent.analyze_compatibility(payload.job_description)
        return analysis
    except AnalysisUnavailable as e:
        raise HTTPException(status_code=503, detail="Compatibility analysis is temporarily unavailable") from e
    except Exception as e:
        logger.exception("Request processing failed")
        raise HTTPException(status_code=500, detail="Request processing failed") from e

@app.post("/api/reset-session")
async def post_reset_session(payload: ResetRequest):
    """Resets conversation memory for a session ID."""
    agent.reset_session(payload.session_id)
    return {"status": "success", "message": "Conversation history cleared."}

@app.get("/api/memory/{session_id}")
async def get_memory(session_id: str):
    """Returns the conversation logs in memory for debug/transparency."""
    logs = agent.get_memory_log(session_id)
    return {"logs": logs}

# Mount static frontend files.
# Make sure frontend folder exists.
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir, exist_ok=True)

# Mount the static files
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
