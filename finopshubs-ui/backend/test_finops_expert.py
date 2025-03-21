"""
Test script for directly testing the FinOps Expert module
Run this script with: python test_finops_expert.py
"""

import os
import sys
import importlib.util
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def load_finops_expert():
    """Load the finops_expert_with_bing_grounding.py module"""
    try:
        # Get the path to the finops_expert_with_bing_grounding.py file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        finops_expert_path = os.path.join(current_dir, "finops_expert_with_bing_grounding.py")
        
        if not os.path.exists(finops_expert_path):
            logger.error(f"FinOps Expert module not found at: {finops_expert_path}")
            return None
        
        logger.info(f"Loading FinOps Expert module from: {finops_expert_path}")
        
        # Add the current directory to Python path
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            logger.info(f"Added {current_dir} to Python path")
        
        # Load the module
        spec = importlib.util.spec_from_file_location("finops_expert", finops_expert_path)
        finops_expert = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(finops_expert)
        
        logger.info(f"Successfully loaded FinOps Expert module")
        
        # List available functions
        functions = [name for name in dir(finops_expert) if callable(getattr(finops_expert, name)) and not name.startswith('_')]
        logger.info(f"Available functions: {', '.join(functions)}")
        
        return finops_expert
    except Exception as e:
        logger.error(f"Failed to load FinOps Expert module: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return None

def test_bing_connection(finops_expert):
    """Test the Bing connection"""
    try:
        logger.info("Testing Bing connection...")
        
        # Try to find the test function
        if hasattr(finops_expert, 'test_bing_connection'):
            result = finops_expert.test_bing_connection()
            logger.info(f"Bing connection test result: {result}")
            return result
        elif hasattr(finops_expert, 'test_bing_sample'):
            result = finops_expert.test_bing_sample()
            logger.info(f"Bing sample test result: {result}")
            return result
        else:
            logger.warning("No Bing test function found")
            return False
    except Exception as e:
        logger.error(f"Error testing Bing connection: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return False

def ask_question(finops_expert, question):
    """Ask a question to the FinOps Expert"""
    try:
        logger.info(f"Asking question: {question}")
        
        if hasattr(finops_expert, 'finops_expert_with_bing'):
            answer = finops_expert.finops_expert_with_bing(question)
            logger.info(f"Got answer (length: {len(answer)})")
            return answer
        else:
            logger.warning("No finops_expert_with_bing function found")
            return "Function not found"
    except Exception as e:
        logger.error(f"Error asking question: {str(e)}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("🧪 Testing FinOps Expert module")
    
    # Load the module
    finops_expert = load_finops_expert()
    
    if finops_expert:
        print("\n✅ Module loaded successfully")
        
        # Test Bing connection
        print("\n🔍 Testing Bing connection...")
        bing_result = test_bing_connection(finops_expert)
        print(f"Bing connection test: {'✅ Success' if bing_result else '❌ Failed'}")
        
        # Ask a test question
        print("\n💬 Asking a test question...")
        test_question = "What is Cloud FinOps?"
        print(f"Question: {test_question}")
        answer = ask_question(finops_expert, test_question)
        print(f"Answer: {answer[:500]}..." if len(answer) > 500 else answer)
    else:
        print("\n❌ Failed to load module")
    
    print("\n✨ Test complete") 