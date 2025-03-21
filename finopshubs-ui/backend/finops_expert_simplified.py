"""
Simplified FinOps Expert module for testing
This is a simplified version that doesn't require Azure credentials
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Example function to return a simple answer
def finops_expert_with_bing(question, config=None):
    """
    Simplified version of the FinOps Expert function
    Returns a static response for testing purposes
    """
    logger.info(f"Received question: {question}")
    
    # Get environment information
    env_info = "\n\nEnvironment:\n"
    env_info += f"- Working directory: {os.getcwd()}\n"
    env_info += f"- Python version: {sys.version}\n"
    env_info += f"- Python path: {sys.path}\n"
    
    # Create a mock response
    response = f"""
# Answer to: {question}

FinOps (Financial Operations) is a framework for managing and optimizing cloud costs through collaboration between finance, technology, and business teams. It helps organizations get maximum business value from their cloud by bringing financial accountability to cloud spending.

Key FinOps principles include:

1. **Visibility & Allocation**: Understanding where cloud costs are coming from
2. **Optimization**: Finding ways to reduce waste and improve efficiency
3. **Forecasting**: Predicting future cloud spend to aid in budgeting
4. **Accountability**: Making teams responsible for their cloud usage
5. **Collaboration**: Breaking down silos between finance and technical teams

This is a simplified response from the FinOps Expert module.

[Microsoft Learn FinOps Documentation](https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/)
[FinOps Foundation](https://www.finops.org/)
{env_info}
"""
    
    return response

def test_bing_connection():
    """Test if Bing connection works"""
    logger.info("Testing Bing connection (simplified version)")
    return True

def test_bing_sample():
    """Alternative test function for Bing"""
    logger.info("Testing Bing with sample (simplified version)")
    return True

# Other utility functions
def list_functions():
    """List all available functions in this module"""
    return [name for name in globals() if callable(globals()[name]) and not name.startswith('_')]

if __name__ == "__main__":
    print("Testing simplified FinOps Expert module")
    question = "What is FinOps?"
    answer = finops_expert_with_bing(question)
    print(f"Question: {question}")
    print(f"Answer: {answer}") 