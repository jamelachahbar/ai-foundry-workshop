"""
Main application entry point.
"""
import os
import logging
import importlib
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import finops

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FinOps Hubs AI API",
    description="API for the FinOps Hubs AI application",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the FinOps expert modules and check capabilities
try:
    # First try to import the Azure AI implementation
    logger.info("Attempting to load FinOps Expert with Azure AI...")
    azure_ai_module = importlib.import_module("finops_expert_azure_ai")
    logger.info("Successfully loaded FinOps Expert with Azure AI")
    USING_AZURE_AI = True
    
    # Check if DeepSeek enhancement is available
    ENHANCEMENT_AVAILABLE = getattr(azure_ai_module, "DEEPSEEK_AVAILABLE", False)
    ENHANCEMENT_ENABLED = getattr(azure_ai_module, "ENHANCEMENT_ENABLED", False)
    logger.info(f"DeepSeek enhancement available: {ENHANCEMENT_AVAILABLE}")
    logger.info(f"DeepSeek enhancement enabled: {ENHANCEMENT_ENABLED}")
    
except ImportError as e:
    logger.warning(f"Failed to load FinOps Expert with Azure AI: {str(e)}")
    logger.info("Attempting to load FinOps Expert with direct Bing integration...")
    ENHANCEMENT_AVAILABLE = False
    ENHANCEMENT_ENABLED = False

    # Try to import the direct Bing integration
    try:
        # Check if file exists first
        finops_expert_file = os.path.join(os.path.dirname(__file__), "finops_expert_with_bing_grounding.py")
        if os.path.exists(finops_expert_file):
            logger.info(f"Found finops_expert_with_bing_grounding.py at {finops_expert_file}")
        else:
            logger.warning(f"File not found: {finops_expert_file}, looking in finopshubs-ai directory")
            # Try alternative location
            alt_path = os.path.join(os.path.dirname(__file__), "..", "..", "finopshubs-ai", "finops_expert_with_bing_grounding.py")
            if os.path.exists(alt_path):
                logger.info(f"Found finops_expert_with_bing_grounding.py at {alt_path}")
            else:
                logger.error(f"Failed to find finops_expert_with_bing_grounding.py")
        
        importlib.import_module("finops_expert_with_bing_grounding")
        logger.info("Successfully loaded FinOps Expert with direct Bing integration")
        USING_AZURE_AI = False
    except ImportError as e:
        logger.error(f"Failed to load FinOps Expert with direct Bing integration: {str(e)}")
        logger.error("Both FinOps Expert modules failed to load")
        USING_AZURE_AI = False

# Include routers
app.include_router(finops.router)

# Add a global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"An internal server error occurred: {str(exc)}"},
    )

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"status": "ok"}

# Root endpoint
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """
    Root endpoint with API information.
    """
    # Get version information from modules if available
    version_info = {}
    
    if USING_AZURE_AI:
        try:
            module = importlib.import_module("finops_expert_azure_ai")
            version_info["azure_ai"] = getattr(module, "__version__", "1.0.0")
        except:
            version_info["azure_ai"] = "Unknown"
    else:
        try:
            module = importlib.import_module("finops_expert_with_bing_grounding")
            version_info["bing_direct"] = getattr(module, "__version__", "1.0.0")
        except:
            version_info["bing_direct"] = "Unknown"
    
    return {
        "name": "FinOps Hubs AI API",
        "version": "0.1.0",
        "status": "running",
        "modules": {
            "finops_expert_azure_ai": USING_AZURE_AI, 
            "finops_expert_bing_direct": not USING_AZURE_AI,
            "deepseek_enhancement": {
                "available": ENHANCEMENT_AVAILABLE,
                "enabled": ENHANCEMENT_ENABLED
            }
        },
        "versions": version_info
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 