from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Request, Response, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
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

# Import the new Azure AI-based FinOps expert
try:
    from finops_expert_azure_ai import finops_expert_with_azure_ai, MOCK_MODE, ENHANCEMENT_ENABLED, test_azure_ai_connection, test_deepseek_connection
    USING_AZURE_AI = True
except ImportError:
    from finops_expert_with_bing_grounding import finops_expert_with_bing, MOCK_MODE
    USING_AZURE_AI = False
    ENHANCEMENT_ENABLED = True

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
    conversation_history: Optional[List[Dict[str, Any]]] = []
    options: Optional[Dict[str, Any]] = None

class Citation(BaseModel):
    number: str
    url: str
    title: str

class AnswerResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    formatted_answer: str

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
@router.post("/ask", response_model=AnswerResponse)
async def ask_finops_question(request: QuestionRequest):
    """
    Process a FinOps question and return an expert answer with citations.
    """
    question = request.question
    conversation_history = request.conversation_history
    options = request.options or {}
    
    logger.info(f"Received question: {question}")
    logger.info(f"Using Azure AI: {USING_AZURE_AI}, Mock Mode: {MOCK_MODE}, Enhancement: {ENHANCEMENT_ENABLED}")
    
    if options:
        logger.info(f"Options provided: {options}")
    
    try:
        # Call the appropriate FinOps expert function
        if USING_AZURE_AI:
            logger.info("Using Azure AI Foundry for FinOps expert")
            # Extract relevant options
            config = {
                "use_mock_mode": options.get("use_mock_mode", MOCK_MODE),
                "enhancement_enabled": options.get("enhancement_enabled", ENHANCEMENT_ENABLED)
            }
            result = finops_expert_with_azure_ai(question, conversation_history, config)
        else:
            logger.info("Using direct Bing integration for FinOps expert")
            result = finops_expert_with_bing(question, conversation_history)
        
        # Log the number of citations
        citation_count = len(result.get("citations", []))
        logger.info(f"Generated answer with {citation_count} citations")
        
        # Return the response
        return result
    except Exception as e:
        logger.error(f"Error processing FinOps question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing your question: {str(e)}"
        )

# Add the expert/ask endpoint to match frontend URL structure
@router.post("/expert/ask", response_model=AnswerResponse)
async def ask_finops_expert_question(request: QuestionRequest):
    """
    Alternative endpoint that matches the frontend URL structure.
    This simply calls the same functionality as the /ask endpoint.
    """
    logger.info("Request received at /expert/ask endpoint - forwarding to main handler")
    return await ask_finops_question(request)

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

@router.get("/config", response_model=Dict[str, Any])
async def get_config():
    """Get the current configuration for the FinOps expert"""
    config = {
        "using_azure_ai": USING_AZURE_AI,
        "mock_mode": MOCK_MODE,
        "enhancement_enabled": ENHANCEMENT_ENABLED
    }
    
    return config

@router.post("/config", response_model=Dict[str, Any])
async def update_config(config: Dict[str, Any] = Body(...)):
    """Update the configuration for the FinOps expert"""
    global MOCK_MODE, ENHANCEMENT_ENABLED
    
    # Store original values to compare if anything changed
    original_config = {
        "mock_mode": MOCK_MODE,
        "enhancement_enabled": ENHANCEMENT_ENABLED
    }
    
    # Update the configuration
    if "mock_mode" in config:
        MOCK_MODE = config["mock_mode"]
    
    if "enhancement_enabled" in config:
        ENHANCEMENT_ENABLED = config["enhancement_enabled"]
    
    # Log the changes
    changes = []
    if original_config["mock_mode"] != MOCK_MODE:
        changes.append(f"Mock mode: {original_config['mock_mode']} -> {MOCK_MODE}")
    
    if original_config["enhancement_enabled"] != ENHANCEMENT_ENABLED:
        changes.append(f"Enhancement: {original_config['enhancement_enabled']} -> {ENHANCEMENT_ENABLED}")
    
    if changes:
        logger.info(f"Configuration updated: {', '.join(changes)}")
    else:
        logger.info("Configuration unchanged")
    
    return {
        "using_azure_ai": USING_AZURE_AI,
        "mock_mode": MOCK_MODE,
        "enhancement_enabled": ENHANCEMENT_ENABLED,
        "changes": changes
    }

@router.get("/test-connections", response_model=Dict[str, Any])
async def test_connections():
    """Test the connections to Azure AI and DeepSeek if available"""
    result = {
        "using_azure_ai": USING_AZURE_AI,
        "mock_mode": MOCK_MODE,
        "enhancement_enabled": ENHANCEMENT_ENABLED
    }
    
    if USING_AZURE_AI:
        if not MOCK_MODE:
            # Test Azure AI connection
            azure_connection = test_azure_ai_connection()
            result["azure_ai_connection"] = azure_connection
        else:
            result["azure_ai_connection"] = "Skipped (Mock mode enabled)"
        
        if ENHANCEMENT_ENABLED:
            # Test DeepSeek connection
            try:
                deepseek_connection = test_deepseek_connection()
                result["deepseek_connection"] = deepseek_connection
            except Exception as e:
                logger.error(f"Error testing DeepSeek connection: {str(e)}")
                result["deepseek_connection"] = f"Error: {str(e)}"
        else:
            result["deepseek_connection"] = "Skipped (Enhancement disabled)"
    else:
        result["error"] = "Azure AI Foundry not available"
    
    return result

# Add more routes as needed 