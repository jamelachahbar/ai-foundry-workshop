"""
Simplified FinOps Expert module for testing
This is a simplified version that doesn't require Azure credentials
"""
import os
import sys
import logging
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
                    except ValueError:
                        logger.warning(f"Invalid line in .env file: {line}")
            return True
        except Exception as e:
            logger.error(f"Error loading .env file: {str(e)}")
            return False
    else:
        logger.warning(f".env file not found at {env_file}")
        return False

# Try to load environment variables from .env file
load_env_file()

# Check if mock mode is enabled
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() in ("true", "1", "yes")

# Predefined sources for various FinOps topics
FINOPS_SOURCES = [
    {
        "title": "Microsoft FinOps Documentation",
        "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/finops/",
        "description": "Official Microsoft documentation on FinOps practices and principles."
    },
    {
        "title": "FinOps Foundation",
        "url": "https://www.finops.org/",
        "description": "The FinOps Foundation is dedicated to advancing the discipline of cloud financial management."
    },
    {
        "title": "Azure Cost Management and Billing Documentation",
        "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/",
        "description": "Comprehensive guide to managing and optimizing costs in Azure."
    },
    {
        "title": "Microsoft Cloud Economics",
        "url": "https://www.microsoft.com/en-us/microsoft-cloud/cloud-economics",
        "description": "Resources for understanding the economic benefits of moving to the cloud."
    },
    {
        "title": "Azure Advisor Cost Recommendations",
        "url": "https://learn.microsoft.com/en-us/azure/advisor/advisor-cost-recommendations",
        "description": "Specific recommendations for optimizing costs in Azure."
    },
    {
        "title": "AWS Well-Architected Framework - Cost Optimization Pillar",
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html",
        "description": "Best practices for cost optimization in AWS cloud environments."
    },
    {
        "title": "Google Cloud Cost Management",
        "url": "https://cloud.google.com/cost-management",
        "description": "Tools and best practices for optimizing costs in Google Cloud."
    },
    {
        "title": "FinOps for Engineers",
        "url": "https://www.finops.org/resources/finops-for-engineers/",
        "description": "Guide on how engineers can apply FinOps principles to their work."
    },
    {
        "title": "Cloud Cost Optimization Best Practices",
        "url": "https://learn.microsoft.com/en-us/azure/well-architected/cost/optimize-checklist",
        "description": "Checklist for optimizing cloud costs based on industry best practices."
    },
    {
        "title": "FinOps Certified Practitioner Certification",
        "url": "https://www.finops.org/certification/",
        "description": "Information about professional FinOps certification programs."
    }
]

# Additional sources for specific topics
TOPIC_SPECIFIC_SOURCES = {
    "reserved_instances": [
        {
            "title": "Azure Reserved Instances Overview",
            "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/save-compute-costs-reservations",
            "description": "How to save on compute costs with Azure Reserved VM Instances."
        },
        {
            "title": "AWS Reserved Instances",
            "url": "https://aws.amazon.com/ec2/pricing/reserved-instances/",
            "description": "Cost savings with AWS EC2 Reserved Instances."
        }
    ],
    "tagging": [
        {
            "title": "Azure Cost Management: Tags Best Practices",
            "url": "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging",
            "description": "Best practices for tagging resources in Azure for cost management."
        },
        {
            "title": "AWS Tagging Strategies",
            "url": "https://aws.amazon.com/blogs/aws-cloud-financial-management/building-an-aws-cost-allocation-strategy-with-tagging/",
            "description": "Building a cost allocation strategy with tagging in AWS."
        }
    ],
    "budget": [
        {
            "title": "Azure Budget Alerts",
            "url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-alerts-monitor-usage-spending",
            "description": "How to set up budget alerts in Azure Cost Management."
        },
        {
            "title": "AWS Budgets",
            "url": "https://aws.amazon.com/aws-cost-management/aws-budgets/",
            "description": "Set custom budgets and receive alerts when costs exceed your threshold."
        }
    ]
}

def simulated_web_search(query: str, count: int = 5) -> List[Dict[str, str]]:
    """
    Simulate a web search for FinOps-related topics
    This would normally use a real web search API like Bing
    """
    logger.info(f"Performing simulated web search for: {query}")
    
    # Look for specific topics in the query
    topic_specific_results = []
    keywords = {
        "reserved_instances": ["reserved", "ri", "savings plan", "commitment"],
        "tagging": ["tag", "tagging", "labels", "allocation", "chargeback", "showback"],
        "budget": ["budget", "alert", "threshold", "spending", "limit"]
    }
    
    # Check for topic-specific keywords
    for topic, topic_keywords in keywords.items():
        if any(keyword in query.lower() for keyword in topic_keywords):
            if topic in TOPIC_SPECIFIC_SOURCES:
                topic_specific_results.extend(TOPIC_SPECIFIC_SOURCES[topic])
    
    # Combine with general results
    # Basic keyword matching to return more relevant sources
    general_keywords = [
        "cost", "billing", "optimize", "reduce", "save", "budget", 
        "governance", "management", "cloud", "azure", "aws", "gcp",
        "finops", "financial", "operations", "accountability"
    ]
    
    # Score general sources
    general_results = []
    for source in FINOPS_SOURCES:
        score = 0
        for keyword in general_keywords:
            if keyword.lower() in query.lower():
                # If the keyword is also in the source title or description, it's more relevant
                source_text = source["title"].lower() + " " + source.get("description", "").lower()
                if keyword.lower() in source_text:
                    score += 2
                else:
                    score += 1
        
        if score > 0:
            general_results.append((source, score))
    
    # Sort general results by score
    general_results.sort(key=lambda x: x[1], reverse=True)
    
    # Combine topic-specific and general results, removing duplicates
    combined_results = []
    seen_urls = set()
    
    # Add topic-specific results first
    for result in topic_specific_results:
        if result["url"] not in seen_urls:
            combined_results.append(result)
            seen_urls.add(result["url"])
    
    # Add general results
    for result, _ in general_results:
        if result["url"] not in seen_urls:
            combined_results.append(result)
            seen_urls.add(result["url"])
    
    return combined_results[:count]  # Return only the requested number of results

def get_relevant_sources(question: str, count: int = 3) -> List[Dict[str, str]]:
    """Return relevant sources based on the question"""
    # In a real implementation, this would query Bing or another search engine
    # For this simplified version, we use our simulated web search
    return simulated_web_search(question, count)

# Function to verify if a link is accessible
def verify_link_accessibility(source: Dict[str, str]) -> Dict[str, str]:
    """Check if a URL is accessible and returns a valid response"""
    url = source.get("url", "")
    if not url:
        return {**source, "is_valid": False}
    
    try:
        # Set a reasonable timeout to avoid long waits
        response = requests.head(url, timeout=3)
        if response.status_code < 400:  # Consider 2xx and 3xx as valid
            return {**source, "is_valid": True}
        else:
            logger.warning(f"Link verification failed for {url}: Status code {response.status_code}")
            return {**source, "is_valid": False}
    except Exception as e:
        logger.warning(f"Link verification failed for {url}: {str(e)}")
        return {**source, "is_valid": False}

def verify_sources(sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Verify multiple sources in parallel using a thread pool"""
    if not sources:
        return []
    
    # Use ThreadPoolExecutor to check links in parallel
    with ThreadPoolExecutor(max_workers=min(5, len(sources))) as executor:
        verified_sources = list(executor.map(verify_link_accessibility, sources))
    
    # Log the results
    valid_count = sum(1 for source in verified_sources if source.get("is_valid", False))
    logger.info(f"Verified {len(sources)} sources. Valid: {valid_count}, Invalid: {len(sources) - valid_count}")
    
    # Sort sources so valid ones come first
    return sorted(verified_sources, key=lambda x: not x.get("is_valid", False))

def finops_expert_with_bing(question: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Simplified version of the FinOps Expert function
    Returns a response with proper citations and sources
    """
    logger.info(f"Processing question: {question}")
    
    # Default config
    if config is None:
        config = {}
    
    # Get relevant sources
    raw_sources = get_relevant_sources(question, count=10)  # Get more sources initially for verification
    
    # Verify the sources if not in mock mode
    if not MOCK_MODE and config.get("verify_links", True):
        sources = verify_sources(raw_sources)
        # Only keep valid sources or at most 2 invalid ones if we don't have enough valid sources
        valid_sources = [s for s in sources if s.get("is_valid", False)]
        invalid_sources = [s for s in sources if not s.get("is_valid", False)][:2]  # Max 2 invalid sources
        
        # Use valid sources first, then add some invalid ones if needed
        if len(valid_sources) >= 3:
            sources = valid_sources[:5]  # Limit to 5 valid sources
        else:
            sources = valid_sources + invalid_sources
            sources = sources[:5]  # Limit to 5 sources total
    else:
        # In mock mode, just use the raw sources
        sources = raw_sources[:5]
    
    # Generate the agent's thought process
    agent_thoughts = generate_agent_thoughts(question, sources)
    
    # Create a final response with citations
    current_time = datetime.now().strftime("%Y-%m-%d")
    
    # Craft a more personalized response based on the question
    if "reserved instances" in question.lower() or "ri" in question.lower():
        response = f"""# Answer to: "{question}"

Reserved Instances (RIs) are a purchasing option in cloud platforms like Azure, AWS, and GCP that offer significant discounts compared to pay-as-you-go pricing. They work by committing to use a specific amount of compute capacity for a fixed period, typically 1 or 3 years.

## Benefits of Reserved Instances:

1. **Cost Savings**: Up to 72% compared to pay-as-you-go pricing, depending on the term commitment
2. **Budgeting Predictability**: Fixed costs for the duration of the reservation
3. **Capacity Reservation**: Ensures capacity in specific availability zones (in some cloud providers)

## Best Practices for RI Management:

1. **Analyze Usage Patterns**: Review your workload patterns before purchasing RIs
2. **Start Small**: Begin with a small portion of your workload to validate the benefits
3. **Regular Review**: Analyze usage and adjust your RI portfolio quarterly
4. **Mixing Commitment Types**: Use a combination of 1-year and 3-year commitments for flexibility
5. **Consider Exchangeability Options**: Some cloud providers allow RI exchanges to adapt to changing needs

## Sources

"""
    elif "tagging" in question.lower() or "tag" in question.lower():
        response = f"""# Answer to: "{question}"

Tagging is a critical component of cloud cost management, enabling organizations to allocate and track costs across different dimensions such as departments, projects, environments, or applications.

## Benefits of a Solid Tagging Strategy:

1. **Cost Allocation**: Accurately distributes costs to the appropriate business units
2. **Accountability**: Creates awareness and responsibility for cloud spending
3. **Budgeting**: Enables more precise budgeting and forecasting
4. **Optimization Opportunities**: Identifies resources that can be optimized or decommissioned
5. **Compliance**: Helps meet regulatory or internal governance requirements

## Effective Tagging Best Practices:

1. **Consistent Naming Convention**: Establish and document standard tag names and formats
2. **Mandatory Tags**: Define which tags must be applied to all resources
3. **Automation**: Use policies and automation to enforce tagging
4. **Regular Audits**: Periodically review resources for missing or incorrect tags
5. **Tag Management Process**: Create a process for requesting new tags or modifying existing ones

## Sources

"""
    elif "budget" in question.lower() or "alert" in question.lower():
        response = f"""# Answer to: "{question}"

Budget alerts are a proactive way to monitor and control cloud spending, providing notifications when costs approach or exceed predefined thresholds.

## Benefits of Budget Alerts:

1. **Cost Control**: Early warning system to prevent unexpected spending
2. **Accountability**: Keeps stakeholders informed about spending patterns
3. **Forecasting**: Helps anticipate future costs based on current spending
4. **Governance**: Enforces financial discipline across the organization
5. **Anomaly Detection**: Identifies unusual spending that may indicate misconfiguration or security issues

## Setting Up Effective Budget Alerts:

1. **Hierarchical Budgets**: Create budgets at multiple levels (organization, department, project)
2. **Multiple Thresholds**: Configure alerts at different percentages (50%, 80%, 90%, 100%)
3. **Actionable Notifications**: Include specific actions recipients should take when receiving alerts
4. **Forecast-Based Alerts**: Set alerts based on projected spending, not just actual costs
5. **Regular Review and Adjustment**: Periodically evaluate and update budget thresholds

## Sources

"""
    else:
        response = f"""# Answer to: "{question}"

FinOps (Financial Operations) is a framework for managing and optimizing cloud costs through collaboration between finance, technology, and business teams. It helps organizations get maximum business value from their cloud spending by bringing financial accountability to cloud usage.

## Key FinOps Principles

1. **Visibility & Allocation**: Understanding where cloud costs are coming from and allocating them to the appropriate teams or projects.
2. **Optimization**: Identifying and eliminating waste, right-sizing resources, and leveraging committed use discounts.
3. **Forecasting**: Predicting future cloud spend to aid in budgeting and planning.
4. **Accountability**: Making teams responsible for their cloud usage and its associated costs.
5. **Collaboration**: Breaking down silos between finance, technology, and business teams.

## Implementation Steps

To implement FinOps in your organization:

1. Establish a FinOps team or center of excellence
2. Define clear cost allocation processes and tagging strategies
3. Implement real-time visibility into cloud spending
4. Create accountability through showback or chargeback models
5. Continuously optimize resources based on utilization data

## Sources

"""

    # Add sources with proper citations in a way that will be detected by the router's markdown link extraction
    for i, source in enumerate(sources, 1):
        is_valid = source.get("is_valid", True)  # Default to True for mock mode
        
        # If we verified the link and it's invalid, add a note
        validity_note = "" if is_valid else " (Note: This link may not be accessible)"
        
        # Create the markdown link
        response += f"[{source['title']}]({source['url']}){validity_note}\n"
    
    # Add note about the simplified module
    if MOCK_MODE:
        response += f"\n\n*Note: This response was generated by the simplified FinOps Expert module using simulated web search results. To get more accurate and up-to-date information, please configure valid API keys in the .env file.*"
    
    # Combine agent thoughts and final response, separated by a special marker
    # that the frontend can use to differentiate them
    combined_response = f"{agent_thoughts}<!-- AGENT_THOUGHT_SEPARATOR -->{response}"
    
    return combined_response

def generate_agent_thoughts(question: str, sources: List[Dict[str, str]]) -> str:
    """Generate agent's thought process for answering a question"""
    thoughts = f"""## Agent Thoughts

I'm analyzing the question: "{question}"

### Key concepts identified:
"""
    
    # Identify key concepts based on keyword matches
    keyword_categories = {
        "finops": ["finops", "financial operations", "cloud financial management", "cost management"],
        "cloud providers": ["azure", "aws", "gcp", "google cloud", "multi-cloud"],
        "cost optimization": ["cost", "saving", "optimize", "reduce", "efficiency"],
        "governance": ["governance", "policy", "compliance", "management"],
        "specific features": ["reserved instances", "tagging", "budget", "alerts", "showback", "chargeback"]
    }
    
    identified_categories = []
    for category, keywords in keyword_categories.items():
        if any(keyword in question.lower() for keyword in keywords):
            identified_categories.append(category)
    
    if identified_categories:
        for category in identified_categories:
            thoughts += f"- {category.title()}\n"
    else:
        thoughts += "- General FinOps question\n"
    
    # Add info about sources
    thoughts += f"\n### Sources identified: {len(sources)}\n"
    for i, source in enumerate(sources, 1):
        is_valid = source.get("is_valid", True)
        validity_status = "✓" if is_valid else "✗"
        thoughts += f"{i}. {validity_status} {source['title']} - {source['url'][:50]}...\n"
    
    # Add reasoning about approach
    thoughts += f"\n### Reasoning:\n"
    
    if any("reserved instances" in question.lower() for keyword in ["reserved", "ri", "commitment"]):
        thoughts += "Question is about Reserved Instances, so I'll focus on explaining the concept, benefits, and best practices for managing RIs.\n"
    elif any(keyword in question.lower() for keyword in ["tag", "tagging"]):
        thoughts += "Question relates to tagging strategy, which is crucial for cost allocation and governance. I'll explain the benefits and best practices.\n"
    elif any(keyword in question.lower() for keyword in ["budget", "alert"]):
        thoughts += "Question is about budget alerts, so I'll focus on explaining how they help with cost management and best practices for setting them up.\n"
    else:
        thoughts += "This appears to be a general FinOps question. I'll provide an overview of FinOps principles and implementation steps.\n"
    
    thoughts += "\nNow I'll structure a comprehensive response with the verified sources."
    
    return thoughts

def test_bing_connection() -> bool:
    """Test if Bing connection works"""
    logger.info("Testing Bing connection")
    
    # In mock mode, always return success
    if MOCK_MODE:
        logger.info("Running in mock mode, Bing connection test simulated")
        return True
    
    # Check if we have a valid API key
    bing_key = os.environ.get("BING_SEARCH_KEY", "")
    if not bing_key or bing_key == "your-bing-search-key":
        logger.error("Invalid or missing Bing Search API key")
        return False
    
    # In a real implementation, we would actually test the connection
    # For simplicity, we'll just return True if the key looks valid
    if len(bing_key) > 20:
        logger.info("Bing API key looks valid")
        return True
    else:
        logger.error("Bing API key appears invalid (too short)")
        return False

def test_bing_sample() -> bool:
    """Alternative test function for Bing"""
    return test_bing_connection()

def get_version() -> str:
    """Return the version of this module"""
    return "1.0.0-simplified"

# Other utility functions
def list_functions():
    """List all available functions in this module"""
    return [name for name in globals() if callable(globals()[name]) and not name.startswith('_')]

if __name__ == "__main__":
    print("="*50)
    print("FinOps Expert Simplified Module")
    print("="*50)
    print(f"Mock Mode: {MOCK_MODE}")
    print(f"Bing Connection Test: {test_bing_connection()}")
    print("-"*50)
    
    test_question = "What is FinOps and how can it help reduce cloud costs?"
    answer = finops_expert_with_bing(test_question)
    print(f"Test Question: {test_question}")
    print("-"*50)
    print(answer) 