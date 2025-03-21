"""
Enhanced server startup script that ensures the FinOps Expert module is available
and properly configured before starting the server.
"""
import os
import sys
import uvicorn
import logging
import importlib.util
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the current directory to Python path
if current_dir not in sys.path:
    sys.path.append(current_dir)
    logger.info(f"Added {current_dir} to Python path")

# Check if the FinOps Expert module exists
finops_expert_path = os.path.join(current_dir, "finops_expert_with_bing_grounding.py")
finops_expert_simplified_path = os.path.join(current_dir, "finops_expert_simplified.py")

# Check environment variables
env_file = os.path.join(current_dir, ".env")
has_env_file = os.path.exists(env_file)

def check_module(path):
    """Check if a module exists and can be loaded"""
    if not os.path.exists(path):
        return False
    
    try:
        module_name = os.path.basename(path).split(".")[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if it has the required functions
        if hasattr(module, "finops_expert_with_bing"):
            return True
        else:
            logger.warning(f"Module {path} exists but does not have finops_expert_with_bing function")
            return False
    except Exception as e:
        logger.error(f"Error loading module {path}: {str(e)}")
        return False

def generate_simplified_if_needed():
    """Create the simplified module if the main one doesn't exist or work"""
    if check_module(finops_expert_path):
        logger.info("Main FinOps Expert module found and loaded successfully")
        return True
    
    logger.warning("Main FinOps Expert module not found or couldn't be loaded")
    
    # Check for simplified version
    if check_module(finops_expert_simplified_path):
        logger.info("Using simplified FinOps Expert module")
        
        # Copy simplified to main name
        try:
            with open(finops_expert_simplified_path, 'r') as f_in:
                content = f_in.read()
            
            with open(finops_expert_path, 'w') as f_out:
                f_out.write(content)
            
            logger.info(f"Copied simplified module to {finops_expert_path}")
            return True
        except Exception as e:
            logger.error(f"Error copying simplified module: {str(e)}")
            return False
    
    logger.error("Neither main nor simplified FinOps Expert module is available")
    return False

if __name__ == "__main__":
    print("="*50)
    print("FinOpsHubs Backend Server")
    print("="*50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check for module
    print("\nChecking FinOps Expert module...")
    if os.path.exists(finops_expert_path):
        print(f"✓ Found: {finops_expert_path}")
    else:
        print(f"✗ Not found: {finops_expert_path}")
        if os.path.exists(finops_expert_simplified_path):
            print(f"✓ Found simplified version: {finops_expert_simplified_path}")
        else:
            print(f"✗ Not found: {finops_expert_simplified_path}")
    
    # Check for .env file
    print("\nChecking .env file...")
    if has_env_file:
        print(f"✓ Found: {env_file}")
    else:
        print(f"✗ Not found: {env_file}")
        print("  Warning: Some features may not work without proper credentials")
    
    # Make sure module is available
    print("\nPreparing module...")
    if generate_simplified_if_needed():
        print("✓ FinOps Expert module is ready")
    else:
        print("✗ FinOps Expert module could not be prepared")
        print("  Warning: API will return errors for FinOps Expert endpoints")
    
    # Import the app after all path setup
    print("\nStarting FastAPI server...")
    from app.main import app
    
    print("\nServer is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop")
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8000) 