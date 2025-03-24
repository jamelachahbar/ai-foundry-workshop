#!/usr/bin/env python3
"""
Script to check environment variables for the FinOps Expert system
"""
import os
import sys
import logging
from dotenv import load_dotenv, find_dotenv, set_key

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check if the dotenv file exists
    dotenv_path = find_dotenv()
    if dotenv_path:
        logger.info(f"Found .env file at: {dotenv_path}")
    else:
        logger.warning("No .env file found!")
    
    # List of important environment variables to check
    important_vars = [
        "PROJECT_CONNECTION_STRING",
        "MODEL_DEPLOYMENT_NAME",
        "BING_CONNECTION_NAME",
        "AZURE_INFERENCE_ENDPOINT",
        "AZURE_INFERENCE_KEY",
        "FINOPS_ENHANCEMENT_ENABLED",
        "FINOPS_DEBUG_MODE"
    ]
    
    # Check each variable
    logger.info("\n===== Environment Variables =====")
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "CONNECTION_STRING" in var or "KEY" in var:
                masked_value = value[:10] + "..." if len(value) > 10 else "***"
                logger.info(f"{var}: {masked_value}")
            else:
                logger.info(f"{var}: {value}")
        else:
            logger.info(f"{var}: NOT SET")
    
    # Update the enhancement flag if needed
    if not os.environ.get("FINOPS_ENHANCEMENT_ENABLED"):
        if dotenv_path:
            answer = input("\nFINOPS_ENHANCEMENT_ENABLED is not set. Would you like to enable it? (y/n): ")
            if answer.lower() == 'y':
                set_key(dotenv_path, "FINOPS_ENHANCEMENT_ENABLED", "true")
                logger.info("Updated .env file with FINOPS_ENHANCEMENT_ENABLED=true")
                logger.info("Please restart your server for the changes to take effect.")
    
    # Check Python environment
    logger.info("\n===== Python Environment =====")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Try to import key modules
    logger.info("\n===== Module Availability =====")
    modules_to_check = [
        "azure.ai.projects",
        "azure.identity",
        "azure.ai.inference",
        "fastapi",
        "uvicorn"
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            logger.info(f"{module}: AVAILABLE")
        except ImportError:
            logger.info(f"{module}: NOT AVAILABLE")

if __name__ == "__main__":
    main() 