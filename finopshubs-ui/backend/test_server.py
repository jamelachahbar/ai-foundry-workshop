import os
import sys
import uvicorn
import logging
from app.main import app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path to find the finops_expert_with_bing_grounding.py module
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    logger.info(f"Added {current_dir} to Python path")

if __name__ == "__main__":
    logger.info("Starting FastAPI server...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Check if the finops_expert_with_bing_grounding.py file exists
    finops_expert_path = os.path.join(current_dir, "finops_expert_with_bing_grounding.py")
    logger.info(f"FinOps Expert module path: {finops_expert_path}")
    logger.info(f"FinOps Expert module exists: {os.path.exists(finops_expert_path)}")
    
    print("Starting FastAPI server at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="127.0.0.1", port=8000) 