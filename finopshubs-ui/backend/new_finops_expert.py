"""
Simplified implementation of the FinOps Expert function that doesn't rely on the extract_insights_from_sources function.
This can be used as a temporary replacement while the main function is being fixed.
"""

import os
import logging
import traceback
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import requests
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('finops_expert')

# Check if mock mode is enabled
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# FinOps common sources (used in mock mode or when API fails)
FINOPS_SOURCES = [
    {
        "title": "What is FinOps? The Complete Guide",
        "url": "https://www.finops.org/introduction/what-is-finops/", 
        "description": "FinOps is shorthand for Cloud Financial Operations or Cloud Financial Management or Cloud Cost Management. It is the practice of bringing financial accountability to the variable spend model of cloud, enabling distributed teams to make business trade-offs between speed, cost, and quality."
    },
    {
        "title": "FinOps in Azure - Microsoft Cost Management", 
        "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/", 
        "description": "The FinOps approach helps organizations to maintain financial accountability in the cloud by establishing a culture of cost awareness. It involves collaboration across finance, engineering, and business teams to balance speed, cost, and quality."
    },
    {
        "title": "Microsoft FinOps Toolkit on GitHub", 
        "url": "https://github.com/microsoft/finops-toolkit", 
        "description": "The Microsoft FinOps Toolkit is a collection of tools, resources, and best practices that help organizations implement FinOps principles and optimize their cloud costs."
    },
    {
        "title": "Azure Cost Management Documentation",
        "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/",
        "description": "Azure Cost Management and Billing helps you understand Azure billing, manage your account and subscriptions, monitor and control costs, and optimize resource use."
    },
    {
        "title": "FinOps Foundation - Cloud FinOps Principles",
        "url": "https://www.finops.org/framework/principles/",
        "description": "The six FinOps principles are: Teams need to collaborate, Everyone takes ownership for their cloud usage, A centralized team drives FinOps, FinOps reports should be accessible and timely, Decisions are driven by business value, and Take advantage of the variable cost model of the cloud."
    }
]

# Topic-specific sources
TOPIC_SPECIFIC_SOURCES = {
    "cost_allocation": [
        {
            "title": "Azure Cost Management tag comparison report",
            "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-allocation-comparison",
            "description": "The cost allocation tag comparison report in Microsoft Cost Management helps you track how costs are allocated to different teams, products, or business units. This report can validate your tagging and cost allocation strategies."
        }
    ],
    "cost_optimization": [
        {
            "title": "Azure Cost Management best practices",
            "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-best-practices",
            "description": "Best practices for cost optimization in Azure include using Azure Advisor recommendations, right-sizing underutilized services, shutting down unused resources, moving IaaS to PaaS services, reserving capacity with reserved instances, and enforcing cost controls with proper governance."
        }
    ],
    "finops_hub": [
        {
            "title": "Implement a cost management solution with FinOps Hub",
            "url": "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/best-practices/data-landing-zone-cost-optimization",
            "description": "The FinOps Hub is a reference implementation that provides cloud cost insights using Azure services like Azure Cost Management, Data Factory, Azure Data Explorer, and Power BI. It enables cost allocation, showback, detailed spending analysis, and actionable optimization recommendations."
        }
    ]
}

def get_mock_sources(question, count=5):
    """Generate mock sources based on the question topic"""
    question_lower = question.lower()
    
    # Check for specific topic matches
    if any(term in question_lower for term in ["tag", "allocation", "chargeback", "showback"]):
        sources = TOPIC_SPECIFIC_SOURCES.get("cost_allocation", [])
    elif any(term in question_lower for term in ["optimize", "reduce cost", "save money", "cheaper"]):
        sources = TOPIC_SPECIFIC_SOURCES.get("cost_optimization", [])
    elif any(term in question_lower for term in ["hub", "finops hub", "data explorer", "power bi"]):
        sources = TOPIC_SPECIFIC_SOURCES.get("finops_hub", [])
    else:
        # Default to general FinOps sources
        sources = FINOPS_SOURCES
    
    # Add general FinOps sources to ensure we have enough
    if len(sources) < count:
        additional_needed = count - len(sources)
        sources += FINOPS_SOURCES[:additional_needed]
    
    # Ensure we don't return more than requested
    return sources[:count]

def finops_expert_with_bing(question: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Simplified FinOps Expert function that uses mock sources to ground responses
    Returns a response with proper citations
    """
    logger.info(f"Processing question: {question}")
    
    # Default config
    if config is None:
        config = {}
    
    # Track if we're using mock/simulated search
    using_simulated_search = True
    
    try:
        # Get relevant sources - in this simplified version, we always use mock sources
        logger.info("Getting relevant mock sources...")
        sources = get_mock_sources(question, count=5)
            
        logger.info(f"Using {len(sources)} sources for response generation")
        
        # Generate a response based on the sources and question
        response = f"# {question}\n\n"
        
        # Information extraction based on sources
        if sources:
            response += "Based on the available information from reputable sources:\n\n"
            
            # Add key insights extracted from sources
            response += "## Key Information\n\n"
            
            # Use static insights instead of extracting from sources
            static_insights = [
                "**FinOps** is the practice of bringing financial accountability to cloud spend, enabling teams to make business trade-offs between speed, cost, and quality",
                "**Cloud Financial Management** involves collaboration between finance, technology and business teams to manage and optimize cloud costs",
                "Effective FinOps requires **visibility**, **optimization**, and **governance** of cloud resources",
                "**Cost allocation** and tagging are essential for attributing cloud spend to business units",
                "Regular **cost reviews** and optimization are necessary to maintain efficient cloud operations",
                "A **centralized team** typically drives FinOps, though everyone should take ownership of their cloud usage",
                "FinOps reports should be **accessible** and **timely** to support decision-making"
            ]
            
            # Add question-specific insights based on keywords
            question_lower = question.lower()
            if "azure" in question_lower or "microsoft" in question_lower:
                static_insights.append("**Azure Cost Management** provides tools for monitoring, allocating, and optimizing your cloud costs")
                static_insights.append("The **Microsoft FinOps Toolkit** on GitHub offers resources and templates for implementing FinOps practices")
            
            if "tool" in question_lower or "software" in question_lower:
                static_insights.append("Common FinOps tools include cloud provider cost management consoles, third-party platforms, and custom dashboards")
            
            if "saving" in question_lower or "optimi" in question_lower:
                static_insights.append("**Rightsizing** resources, using **reserved instances**, and implementing **auto-scaling** are key optimization strategies")
            
            # Add insights to response
            for insight in static_insights[:8]:  # Limit to 8 insights
                response += f"- {insight}\n"
        else:
            # Fallback to general information if no sources
            response += "Based on FinOps best practices and cloud cost management principles, here's what you should know:\n\n"
            response += "## Key Information\n\n"
            response += "- **Visibility**: Ensure all cloud costs are tracked and understood\n"
            response += "- **Accountability**: Assign ownership of costs to appropriate teams\n"
            response += "- **Optimization**: Regularly review and optimize resource usage\n"
            response += "- **Forecasting**: Project future costs to improve budgeting\n"
            response += "- **Collaboration**: Foster communication between finance, engineering, and business units\n"
        
        # Add citations to the sources
        if sources:
            response += "\n\n## References\n"
            # Track URLs to avoid duplicates
            seen_urls = set()
            
            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                is_valid = source.get("is_valid", True)
                
                # Skip if we've already included this URL or if URL is empty
                if not url or url in seen_urls:
                    continue
                    
                seen_urls.add(url)
                
                # Use a more descriptive link text based on the title
                if is_valid:
                    response += f"\n{i}. [{title}]({url})"
                else:
                    response += f"\n{i}. [{title}]({url}) (Note: This link may not be accessible)"
        
        # Add a note about using simulated search
        if using_simulated_search:
            response += "\n\n---\n\n**Note:** This response is using preconfigured sample search results. Real-time web search is not available due to API configuration."
        
        logger.info("Response generation complete")
        return response
        
    except Exception as e:
        logger.error(f"Error in finops_expert_with_bing: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a fallback response on error
        return f"""# {question}

## Error Processing Your Question

I apologize, but I encountered an error while processing your question. Here's what I can tell you about FinOps:

- **FinOps** (Cloud Financial Operations) is the practice of bringing financial accountability to cloud spend
- It enables teams to make business trade-offs between speed, cost, and quality
- Key pillars include visibility, optimization, and governance of cloud resources
- Effective FinOps requires collaboration between finance, technology, and business teams

For more detailed information, please try again later or rephrase your question.

---

**Note:** This is a fallback response due to a processing error.
"""

if __name__ == "__main__":
    try:
        print("\n🤖 FinOps Toolkit Expert with Mock Sources")
        print("------------------------------------------------")
        
        # Basic menu
        print("\nOptions:")
        print("1. Ask a FinOps question")
        print("2. Exit")
        
        choice = input("\nSelect an option (1-2): ")
        
        if choice == "1":
            question = input("\nEnter your FinOps question: ")
            answer = finops_expert_with_bing(question)
            print("\n🔍 Answer:")
            print(answer)
            
        elif choice == "2":
            print("Exiting...")
            sys.exit(0)
            
        else:
            print("Invalid choice. Please select 1 or 2.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc()) 