from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Request, Response, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os
import logging
from typing import Dict, Any, Optional, List
import time
import asyncio
import io
import importlib.util
import json
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path to the finops_expert_with_bing_grounding.py file
FINOPS_EXPERT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "finops_expert_with_bing_grounding.py"
)

# Path to the simplified version of the module
FINOPS_EXPERT_SIMPLIFIED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "finops_expert_simplified.py"
)

# Create router
router = APIRouter(
    prefix="/api/finops",
    tags=["finops"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    options: Optional[Dict[str, Any]] = None

class AnswerResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, str]]] = None

# Global variable to cache the module
_finops_expert_module = None

# Load the finops_expert module dynamically
def load_finops_expert():
    """Tries to load the finops_expert module, with fallback to simplified version"""
    global _finops_expert_module
    
    # Return cached module if available
    if _finops_expert_module is not None:
        return _finops_expert_module
    
    # First try the main module
    finops_expert = _try_load_module(FINOPS_EXPERT_PATH, "finops_expert")
    if finops_expert:
        logger.info("Successfully loaded main FinOps Expert module")
        _finops_expert_module = finops_expert
        return finops_expert
    
    # If main module fails, try the simplified version
    logger.warning("Main FinOps Expert module could not be loaded, trying simplified version")
    finops_expert = _try_load_module(FINOPS_EXPERT_SIMPLIFIED_PATH, "finops_expert_simplified")
    if finops_expert:
        logger.info("Successfully loaded simplified FinOps Expert module")
        _finops_expert_module = finops_expert
        return finops_expert
    
    # If both fail, return None
    logger.error("Both main and simplified FinOps Expert modules could not be loaded")
    return None

def get_finops_expert():
    """Dependency injection for FastAPI to get the FinOps Expert module"""
    finops_expert = load_finops_expert()
    if finops_expert is None:
        raise HTTPException(status_code=500, detail="FinOps Expert module not available")
    return finops_expert

def _try_load_module(module_path, module_name):
    """Helper function to try loading a module"""
    try:
        if not os.path.exists(module_path):
            logger.warning(f"Module not found at: {module_path}")
            return None
        
        logger.info(f"Loading module from {module_path}")
        
        # Add the directory containing the module to sys.path
        module_dir = os.path.dirname(module_path)
        if module_dir not in sys.path:
            sys.path.append(module_dir)
            logger.info(f"Added {module_dir} to sys.path")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Log available functions
        functions = [name for name in dir(module) if callable(getattr(module, name)) and not name.startswith('_')]
        logger.info(f"Available functions in module: {', '.join(functions)}")
        
        return module
    except Exception as e:
        logger.error(f"Failed to load module {module_name}: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return None

# Simple test endpoint that doesn't require the external module
@router.get("/test")
async def test_api():
    return {"status": "ok", "message": "FinOps API is working"}

# Routes
@router.post("/expert/ask", response_model=AnswerResponse)
async def ask_finops_question(question_request: QuestionRequest):
    try:
        # Load the finops_expert module
        finops_expert = load_finops_expert()
        
        # If module couldn't be loaded, raise an appropriate error
        if finops_expert is None:
            logger.error(f"FinOps Expert module not available for question: {question_request.question}")
            raise HTTPException(
                status_code=500,
                detail="FinOps Expert module is not available. Please check server logs."
            )
        
        # Extract any options from the request
        options = question_request.options if question_request.options else {}
        
        # Call the finops_expert_with_bing function with options
        logger.info(f"Processing FinOps question: {question_request.question}")
        answer = finops_expert.finops_expert_with_bing(question_request.question, config=options)
        
        # Extract sources if available in the answer text
        sources = []
        # Simple extraction of markdown links as sources
        import re
        markdown_links = re.findall(r'\[(.*?)\]\((https?://[^\s)]+)\)', answer)
        for title, url in markdown_links:
            # Check if this is already in the sources list (avoid duplicates)
            if not any(s.get("url") == url for s in sources):
                sources.append({
                    "title": title,
                    "url": url,
                    "description": f"Source for information on {title}"
                })
        
        logger.info(f"Extracted {len(sources)} sources from response")
        return AnswerResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Error processing FinOps question: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)}"
        )

@router.post("/expert/test-bing")
async def test_bing_connection():
    try:
        # Load the finops_expert module
        finops_expert = load_finops_expert()
        
        # If module couldn't be loaded, raise an error
        if finops_expert is None:
            logger.error("FinOps Expert module not available for Bing connection test")
            raise HTTPException(
                status_code=500,
                detail="FinOps Expert module is not available. Please check server logs."
            )
        
        # Call the test_bing_connection function
        logger.info("Testing Bing connection")
        try:
            result = finops_expert.test_bing_connection()
            
            if result:
                return {"success": True, "message": "Bing connection test successful"}
            else:
                return {"success": False, "message": "Bing connection test failed"}
        except AttributeError:
            # If test_bing_connection is not available, try test_bing_sample
            logger.info("test_bing_connection not found, trying test_bing_sample")
            try:
                result = finops_expert.test_bing_sample()
                if result:
                    return {"success": True, "message": "Bing connection test successful (using sample)"}
                else:
                    return {"success": False, "message": "Bing connection test failed (using sample)"}
            except AttributeError:
                logger.error("Neither test_bing_connection nor test_bing_sample functions are available")
                raise HTTPException(
                    status_code=500,
                    detail="Neither test_bing_connection nor test_bing_sample functions are available in the FinOps Expert module"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Bing connection: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Bing connection: {str(e)}"
        )

# Advanced configuration endpoint
@router.post("/expert/configure", status_code=200)
async def configure_finops_expert(config: Dict[str, Any] = Body(default={})):
    """Update configuration for the FinOps Expert module"""
    try:
        # Load the finops_expert module
        finops_expert = load_finops_expert()
        
        if finops_expert is None:
            logger.error("FinOps Expert module not available for configuration")
            raise HTTPException(
                status_code=500,
                detail="FinOps Expert module is not available. Please check server logs."
            )
        
        # Log available functions to help with debugging
        functions = [name for name in dir(finops_expert) if callable(getattr(finops_expert, name)) and not name.startswith('_')]
        logger.info(f"Available functions in module: {', '.join(functions)}")
        
        # We don't actually update any module-level configuration
        # This is just to check if the module loaded correctly
        
        return {
            "success": True, 
            "message": "FinOps Expert module loaded successfully",
            "available_functions": functions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring FinOps Expert: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring FinOps Expert: {str(e)}"
        )

# Health check for the FinOps Expert module
@router.get("/expert/health")
async def health_check():
    """Check if the FinOps Expert module is available"""
    finops_expert = load_finops_expert()
    
    if finops_expert:
        # Get available functions
        functions = [name for name in dir(finops_expert) if callable(getattr(finops_expert, name)) and not name.startswith('_')]
        
        return {
            "status": "ok",
            "version": getattr(finops_expert, "__version__", "unknown"),
            "message": "FinOps Expert module is available",
            "module_type": "real" if os.path.basename(FINOPS_EXPERT_PATH) == "finops_expert_with_bing_grounding.py" else "simplified",
            "functions": functions[:5]  # Show only the first 5 functions to avoid clutter
        }
    else:
        return {
            "status": "error",
            "message": "FinOps Expert module is not available"
        }

# Add more routes as needed 