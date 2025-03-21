"""
FastAPI Backend for FinOps Expert with Bing Grounding

This application serves as the backend for the FinOps Expert UI, providing:
- REST API endpoints for asking FinOps questions
- Server-sent events for streaming responses
- Integration with the FinOps Expert script
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import traceback
import importlib.util
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the FinOps Expert script
try:
    # Get the absolute path of the finops_expert_with_bing_grounding.py file
    finops_expert_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", "..", 
        "finopshubs-ai", 
        "finops_expert_with_bing_grounding.py"
    ))
    
    # Import the module dynamically
    spec = importlib.util.spec_from_file_location("finops_expert_with_bing_grounding", finops_expert_path)
    finops_expert = importlib.util.module_from_spec(spec)
    sys.modules["finops_expert_with_bing_grounding"] = finops_expert
    spec.loader.exec_module(finops_expert)
    
    logger.info(f"Successfully imported FinOps Expert from {finops_expert_path}")
except Exception as e:
    logger.error(f"Failed to import FinOps Expert script: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# FastAPI App Configuration
app = FastAPI(
    title="FinOps Expert API",
    description="""
    FinOps Expert API for Azure cost management and optimization.
    
    This API provides access to:
    - FinOps expertise with Bing grounding for real-time web information
    - Microsoft FinOps Toolkit resources and best practices
    - Azure cost management guidance
    """,
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class FinOpsQuestion(BaseModel):
    question: str
    options: Optional[Dict[str, Any]] = None

class FinOpsResponse(BaseModel):
    answer: str
    citations: Optional[List[Dict[str, str]]] = None

# Routes
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root endpoint to docs."""
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service status."""
    return {"status": "ok"}

@app.post("/api/finops/ask")
async def ask_finops_question(question_data: FinOpsQuestion):
    """
    Ask a FinOps question using the FinOps Expert with Bing grounding.
    """
    try:
        # Configure options
        config = question_data.options or {
            'enhancement_enabled': True,
            'quality_check_enabled': False,  # Disabled by default to avoid timeouts
            'auto_improve_enabled': False,   # Disabled by default to avoid timeouts
            'quality_threshold': 6,
            'cleanup_agent': True,
            'force_github_knowledge': True
        }
        
        # Call the FinOps Expert function
        answer = finops_expert.finops_expert_with_bing(question_data.question, config)
        
        return FinOpsResponse(
            answer=answer,
            citations=[]  # The citations are already included in the answer text
        )
    except Exception as e:
        logger.error(f"Error processing FinOps question: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/api/finops/ask_stream")
async def ask_finops_question_stream(question_data: FinOpsQuestion):
    """
    Ask a FinOps question with streaming response using server-sent events.
    """
    async def event_generator():
        try:
            # Send initial message
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "status",
                    "content": "Processing your question. Please wait..."
                })
            }
            
            # Configure options - always disable quality checks for streaming
            config = question_data.options or {}
            config.update({
                'enhancement_enabled': True,
                'quality_check_enabled': False,
                'auto_improve_enabled': False,
                'cleanup_agent': True,
                'force_github_knowledge': True
            })
            
            # Set up the project client and agent (but don't actually process the question yet)
            if not finops_expert.project_client or not finops_expert.bing_connection:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "content": "Error initializing FinOps Expert. Please check your environment variables."
                    })
                }
                return
            
            # Create the agent
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "status", 
                    "content": "Creating FinOps agent..."
                })
            }
            finops_agent = finops_expert.create_finops_bing_agent()
            
            if not finops_agent:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "content": "Failed to create FinOps agent. Please try again later."
                    })
                }
                return
            
            # Process the question with status updates
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "status",
                    "content": "Sending question to FinOps agent..."
                })
            }
            
            # Get Bing-grounded answer
            bing_result = finops_expert.ask_finops_question_with_bing(finops_agent, question_data.question)
            
            if not bing_result:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "error",
                        "content": "Failed to get answer from FinOps agent."
                    })
                }
                return
            
            # Check if we have bing URLs
            bing_urls = bing_result.get("bing_urls", [])
            if not bing_urls:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "status",
                        "content": "No Bing search results found. Using internal knowledge."
                    })
                }
            else:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "status",
                        "content": f"Found {len(bing_urls)} relevant sources."
                    })
                }
            
            # Enhance with DeepSeek if enabled
            if config.get('enhancement_enabled', True) and finops_expert.deepseek_client:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "type": "status",
                        "content": "Enhancing answer with DeepSeek-R1..."
                    })
                }
                answer = finops_expert.enhance_with_deepseek(question_data.question, bing_result)
            else:
                answer = bing_result["answer"]
            
            # Clean up the agent
            if config.get('cleanup_agent', True):
                try:
                    finops_expert.project_client.agents.delete_agent(finops_agent.id)
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "status",
                            "content": "Cleaning up resources..."
                        })
                    }
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete agent: {str(cleanup_error)}")
            
            # Send the final answer
            yield {
                "event": "result",
                "data": json.dumps({
                    "answer": answer,
                    "citations": bing_urls
                })
            }
            
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            logger.error(traceback.format_exc())
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "content": f"Error processing question: {str(e)}"
                })
            }
    
    return EventSourceResponse(event_generator())

@app.post("/api/finops/test-bing")
async def test_bing_connection():
    """
    Test the Bing connection and return the result.
    """
    try:
        result = finops_expert.test_bing_connection()
        return {
            "success": result,
            "message": "Bing connection test successful!" if result else "Bing connection test failed."
        }
    except Exception as e:
        logger.error(f"Error testing Bing connection: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error testing Bing connection: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 