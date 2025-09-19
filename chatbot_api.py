#!/usr/bin/env python3
"""
FastAPI endpoints for the chatbot
Provides REST API access to the knowledge assistant functionality
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Import the agent functions
from agent import (
    create_kb_agent, create_sql_agent, 
    create_kb_task, create_sql_task,
    save_conversation_to_dynamodb, 
    get_conversation_history_from_dynamodb,
    logger
)

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Chatbot API",
    description="REST API for the Knowledge Base Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    timestamp: str
    agents_used: List[str]

class ChatHistoryResponse(BaseModel):
    session_id: str
    conversations: List[dict]
    total_count: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Global variables for agents (initialized once)
kb_agent = None
sql_agent = None

def initialize_agents():
    """Initialize agents once at startup"""
    global kb_agent, sql_agent
    
    try:
        logger.info("Initializing agents for API...")
        
        # Create Knowledge Base Agent
        kb_agent = create_kb_agent()
        if kb_agent is None:
            logger.error("Failed to create Knowledge Base agent")
            raise Exception("Knowledge Base agent initialization failed")
        
        # Create SQL Agent
        sql_agent = create_sql_agent()
        if sql_agent is None:
            logger.warning("SQL agent not available - continuing without database functionality")
        
        logger.info("Agents initialized successfully for API")
        
    except Exception as e:
        logger.error(f"Error initializing agents: {e}")
        raise e

# Initialize agents at startup
@app.on_event("startup")
async def startup_event():
    """Initialize agents when the API starts"""
    try:
        initialize_agents()
        logger.info("API startup completed successfully")
    except Exception as e:
        logger.error(f"API startup failed: {e}")
        raise e

def get_agents():
    """Dependency to get initialized agents"""
    if kb_agent is None:
        raise HTTPException(status_code=500, detail="Knowledge Base agent not initialized")
    return kb_agent, sql_agent

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, agents=Depends(get_agents)):
    """
    Chat endpoint - Send a message and get a response
    
    - **message**: The user's question/message
    - **session_id**: Optional session ID for continuing a conversation
    """
    try:
        kb_agent, sql_agent = agents
        
        # Generate or use provided session ID
        if request.session_id:
            session_id = request.session_id
            logger.info(f"Continuing session: {session_id}")
        else:
            session_id = f"api_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            logger.info(f"Starting new session: {session_id}")
        
        # Get conversation history for context
        conversation_history = get_conversation_history_from_dynamodb(session_id, limit=5)
        logger.info(f"Retrieved {len(conversation_history)} previous conversations")
        
        # Prepare agents and tasks
        agents_list = []
        tasks = []
        agents_used = []
        
        # Add Knowledge Base Agent (always available)
        if kb_agent:
            agents_list.append(kb_agent)
            kb_task = create_kb_task(request.message, conversation_history, kb_agent)
            tasks.append(kb_task)
            agents_used.append("Knowledge Base")
            logger.info("Knowledge Base agent added to crew")
        
        # Add SQL Agent (if available)
        if sql_agent:
            agents_list.append(sql_agent)
            sql_task = create_sql_task(request.message, conversation_history, sql_agent)
            tasks.append(sql_task)
            agents_used.append("SQL Assistant")
            logger.info("SQL agent added to crew")
        
        if not agents_list:
            raise HTTPException(status_code=500, detail="No agents available")
        
        # Run the crew
        from crewai import Crew, Process
        crew = Crew(
            agents=agents_list,
            tasks=tasks,
            verbose=False,
            process=Process.sequential
        )
        
        logger.info("Starting crew execution...")
        crew_output = crew.kickoff()
        logger.info("Crew execution completed")
        
        # Extract response
        if hasattr(crew_output, 'raw_output'):
            response_text = crew_output.raw_output
            logger.info("Using raw_output from crew result")
        elif hasattr(crew_output, 'result'):
            response_text = crew_output.result
            logger.info("Using result from crew output")
        else:
            response_text = str(crew_output)
            logger.info("Using string representation of crew output")
        
        # Save conversation to DynamoDB
        save_success = save_conversation_to_dynamodb(session_id, request.message, response_text)
        if not save_success:
            logger.warning("Failed to save conversation to DynamoDB")
        
        # Prepare response
        timestamp = datetime.now().isoformat()
        
        return ChatResponse(
            session_id=session_id,
            message=request.message,
            response=response_text,
            timestamp=timestamp,
            agents_used=agents_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/chathistory/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a specific session
    
    - **session_id**: The session ID to retrieve history for
    - **limit**: Maximum number of conversations to return (default: 50)
    """
    try:
        logger.info(f"Retrieving chat history for session: {session_id}")
        
        # Get conversation history from DynamoDB
        conversations = get_conversation_history_from_dynamodb(session_id, limit=limit)
        
        if not conversations:
            logger.warning(f"No conversations found for session: {session_id}")
            return ChatHistoryResponse(
                session_id=session_id,
                conversations=[],
                total_count=0
            )
        
        logger.info(f"Retrieved {len(conversations)} conversations for session {session_id}")
        
        return ChatHistoryResponse(
            session_id=session_id,
            conversations=conversations,
            total_count=len(conversations)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if agents are initialized
        if kb_agent is None:
            return {"status": "unhealthy", "reason": "Knowledge Base agent not initialized"}
        
        return {
            "status": "healthy",
            "knowledge_base_agent": "available",
            "sql_agent": "available" if sql_agent else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "reason": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat - Send a message and get a response",
            "history": "GET /chathistory/{session_id} - Get chat history for a session",
            "health": "GET /health - Health check"
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    print(f"🚀 Starting Chatbot API server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "chatbot_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
