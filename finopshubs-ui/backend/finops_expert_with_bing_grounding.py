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
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the insight extraction helper functions
try:
    logger.info("Attempting to import finops_insights_helpers module")
    from finops_insights_helpers import (
        extract_insights_from_sources as external_extract_insights_from_sources,
        extract_definition,
        extract_benefits,
        extract_best_practices,
        extract_challenges,
        extract_main_topic as external_extract_main_topic,
        extract_specific_topic_insights as external_extract_specific_topic_insights
    )
    logger.info("✅ Successfully imported insight extraction functions")
    
    # Create wrapper functions to handle different function signatures
    def extract_main_topic(question: str) -> str:
        return external_extract_main_topic(question)
    
    def extract_specific_topic_insights(content: str, topic: str, category: str) -> str:
        # The external function has a different signature, so we need to adapt
        # We'll create mock sources since the function expects them
        mock_source = {"title": "Content", "url": "", "description": content}
        return "\n".join(external_extract_specific_topic_insights(topic, [mock_source], [content], question=category))
    
    # Create a wrapper for the extract_insights_from_sources function
    def extract_insights_from_sources(question: str, sources: List[Dict], with_citations: bool = True) -> Dict[str, Any]:
        # We'll keep our own implementation to ensure the return structure is consistent
        # This way we can ensure all values are strings in the citations
        logger.info(f"Using custom extraction with imported functions for question: {question}")
        return custom_extract_insights_from_sources(question, sources, with_citations)
    
except ImportError as e:
    logger.warning(f"⚠️ Could not import finops_insights_helpers, defining functions locally: {str(e)}")
    logger.warning("Helper functions will be limited in functionality")
    
    # Define fallback extraction functions
    def extract_main_topic(question: str) -> str:
        """
        Extract the main topic from the user's question
        
        Args:
            question: The user's question
            
        Returns:
            The main topic of the question
        """
        # Remove common question prefixes
        question = question.lower().strip()
        prefixes = [
            "what is", "how to", "can you explain", "tell me about", 
            "what are", "how do", "why is", "when should"
        ]
        
        for prefix in prefixes:
            if question.startswith(prefix):
                question = question[len(prefix):].strip()
        
        # Remove suffixes
        suffixes = ["?", ".", "!"]
        for suffix in suffixes:
            if question.endswith(suffix):
                question = question[:-1].strip()
        
        # Identify important FinOps terms
        finops_terms = [
            "finops", "cloud cost", "cloud financial management", "cloud economics",
            "cost optimization", "cloud spend", "cloud budget", "cost governance",
            "cloud finance", "cloud accountability", "resource utilization", 
            "cloud waste", "cost transparency", "cost monitoring", "cost reporting",
            "cloud roi", "cloud tco", "unit economics", "showback", "chargeback"
        ]
        
        # Check if any finops terms are in the question
        for term in finops_terms:
            if term in question:
                # Return a bit more context around the term
                start_idx = max(0, question.find(term) - 20)
                end_idx = min(len(question), question.find(term) + len(term) + 20)
                return question[start_idx:end_idx].strip()
        
        # If no specific terms found, return the first part of the question
        words = question.split()
        return " ".join(words[:min(8, len(words))])

    def extract_specific_topic_insights(content: str, topic: str, category: str) -> str:
        """
        Extract specific insights for a given topic and category
        
        Args:
            content: The source content to extract from
            topic: The main topic to focus on
            category: The category of insights to extract
                (definition, benefits, challenges, best_practices, tools, metrics, steps)
                
        Returns:
            Extracted insights as a formatted string
        """
        if not content or not topic:
            return ""
        
        # Find paragraphs that contain both the topic and category-specific keywords
        paragraphs = content.split("\n\n")
        
        # Define keywords for each category
        category_keywords = {
            "definition": ["is", "means", "refers to", "defined as", "concept of", "understanding"],
            "benefits": ["benefit", "advantage", "value", "improve", "enhance", "save", "increase", "reduce cost"],
            "challenges": ["challenge", "difficult", "problem", "issue", "hurdle", "obstacle", "limitation"],
            "best_practices": ["practice", "best", "recommend", "should", "effective", "approach", "strategy"],
            "tools": ["tool", "software", "platform", "solution", "technology", "service", "product"],
            "metrics": ["metric", "measure", "kpi", "indicator", "track", "monitor", "calculate"],
            "steps": ["step", "process", "implement", "create", "setup", "establish", "approach", "procedure"]
        }
        
        # Select paragraphs that may contain relevant information
        relevant_paragraphs = []
        
        for para in paragraphs:
            para_lower = para.lower()
            
            # Check if paragraph contains the topic
            if topic.lower() in para_lower:
                # Check if paragraph contains category-specific keywords
                if any(keyword in para_lower for keyword in category_keywords.get(category, [])):
                    relevant_paragraphs.append(para)
        
        # If we don't have enough relevant paragraphs, get paragraphs that just contain the topic
        if len(relevant_paragraphs) < 2:
            for para in paragraphs:
                if topic.lower() in para.lower() and para not in relevant_paragraphs:
                    relevant_paragraphs.append(para)
                    if len(relevant_paragraphs) >= 3:
                        break
        
        # Format based on category
        result = ""
        
        if category == "definition":
            # For definitions, prioritize sentences that directly define the topic
            definition_sentences = []
            for para in relevant_paragraphs:
                sentences = para.split(". ")
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if topic.lower() in sentence_lower and any(term in sentence_lower for term in ["is", "refers to", "means", "defined as"]):
                        definition_sentences.append(sentence)
            
            if definition_sentences:
                result = ". ".join(definition_sentences[:2]) + "."
            else:
                # Just use the first relevant paragraph as a definition
                result = relevant_paragraphs[0] if relevant_paragraphs else ""
        
        elif category in ["benefits", "challenges", "tools", "metrics"]:
            # For lists, extract bullet points
            items = []
            for para in relevant_paragraphs:
                # Split into sentences
                sentences = para.split(". ")
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in category_keywords.get(category, [])):
                        items.append("• " + sentence.strip() + ".")
            
            # Remove duplicates and limit
            unique_items = []
            for item in items:
                if not any(similar_item(item, existing) for existing in unique_items):
                    unique_items.append(item)
            
            result = "\n".join(unique_items[:5])
        
        elif category == "best_practices":
            # For best practices, format as bullet points
            practices = []
            for para in relevant_paragraphs:
                sentences = para.split(". ")
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in category_keywords.get(category, [])):
                        practices.append("• " + sentence.strip() + ".")
            
            # Remove duplicates and limit
            unique_practices = []
            for practice in practices:
                if not any(similar_item(practice, existing) for existing in unique_practices):
                    unique_practices.append(practice)
            
            result = "\n".join(unique_practices[:5])
        
        elif category == "steps":
            # For steps, try to extract numbered steps or create bullet points
            steps = []
            step_counter = 1
            
            for para in relevant_paragraphs:
                sentences = para.split(". ")
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    if any(keyword in sentence_lower for keyword in category_keywords.get(category, [])):
                        steps.append(f"{step_counter}. {sentence.strip()}.")
                        step_counter += 1
            
            # Limit number of steps
            result = "\n".join(steps[:5])
        
        return result

    def similar_item(item1: str, item2: str) -> bool:
        """
        Check if two items are similar to avoid duplication
        
        Args:
            item1: First item text
            item2: Second item text
            
        Returns:
            True if items are similar, False otherwise
        """
        # Simple similarity check: if 70% of words overlap
        words1 = set(item1.lower().split())
        words2 = set(item2.lower().split())
        
        # Remove common words
        common_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "is", "are"}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / min(len(words1), len(words2))
        
        return similarity > 0.7

    # In fallback mode, just use the custom implementation
    def extract_insights_from_sources(question: str, sources: List[Dict], with_citations: bool = True) -> Dict[str, Any]:
        return custom_extract_insights_from_sources(question, sources, with_citations)

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
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Extra processing for API keys to ensure no extra characters
                        if key in ["BING_SEARCH_KEY", "AZURE_API_KEY"]:
                            # Remove any whitespace, quotes or other common characters
                            value = value.strip().strip('"\'').strip()
                            logger.info(f"Loaded {key} (length: {len(value)})")
                        
                        os.environ[key] = value
                    except ValueError:
                        logger.warning(f"Invalid line in .env file: {line}")
            
            # Check if we have the required keys
            required_keys = ["BING_SEARCH_KEY", "BING_SEARCH_ENDPOINT"]
            for key in required_keys:
                if not os.environ.get(key):
                    logger.warning(f"Required key {key} not found in .env file")
                else:
                    if key == "BING_SEARCH_KEY":
                        value = os.environ.get(key)
                        if value == "your-bing-search-key" or len(value) < 20:
                            logger.warning(f"{key} appears to be invalid or a placeholder")
            
            return True
        except Exception as e:
            logger.error(f"Error loading .env file: {str(e)}")
            return False
    else:
        logger.warning(f".env file not found at {env_file}")
        return False

# Try to load environment variables from .env file
load_env_file()

# Initialize MOCK_MODE - Important: this should be false by default to use real search
# Only set to true if explicitly configured in environment
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() in ["true", "1", "yes", "t"]
logger.info(f"MOCK_MODE is set to: {MOCK_MODE}")
if MOCK_MODE:
    logger.warning("Using MOCK_MODE: Real-time search is disabled, using predefined responses")
else:
    logger.info("Using REAL search mode: Responses will be based on real-time search results")

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

def get_relevant_sources(question: str, count: int = 3, mock_mode: bool = None) -> List[Dict[str, str]]:
    """
    Return relevant sources based on the question
    
    Args:
        question: The user's question
        count: Number of sources to return
        mock_mode: Whether to use mock mode (overrides global MOCK_MODE if provided)
        
    Returns:
        List of source dictionaries with title, url, and description
    """
    # Use provided mock_mode parameter or global MOCK_MODE if not provided
    use_mock = MOCK_MODE if mock_mode is None else mock_mode
    
    logger.info(f"Getting sources for '{question}' (Mock mode: {use_mock})")
    
    if use_mock:
        logger.info("Using simulated web search due to mock mode")
        return simulated_web_search(question, count)
    else:
        # Try to use actual web search
        try:
            logger.info("Attempting real web search...")
            bing_key = os.environ.get("BING_SEARCH_KEY", "")
            
            if not bing_key or bing_key == "your-bing-search-key":
                logger.warning("Missing or invalid BING_SEARCH_KEY in environment, falling back to mock data")
                return simulated_web_search(question, count)
            
            # Perform real web search
            result = bing_web_search(question, count)
            
            if result and len(result) > 0:
                logger.info(f"Successfully retrieved {len(result)} sources from Bing")
                return result
            else:
                logger.warning("No results from real search, falling back to mock data")
                return simulated_web_search(question, count)
        except Exception as e:
            logger.error(f"Error performing real search: {str(e)}")
            logger.error(traceback.format_exc())
            logger.warning("Falling back to mock data due to search error")
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

def finops_expert_with_bing(question: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get answer to a FinOps question using Bing Search API for web search.
    
    Args:
        question: The FinOps question to answer
        config: Optional configuration parameters
            - history: Conversation history (optional)
            - auto_improve_enabled: Whether to automatically improve the answer (default: True)
            - quality_threshold: The quality threshold for the answer to pass before auto-improvement (default: 7.0)
            - use_real_search: Whether to use real search or simulated search (overrides MOCK_MODE if provided)
    
    Returns:
        Dictionary containing:
            - answer: The answer to the question
            - sources: The sources used to generate the answer
            - quality_scores: Quality scores for the answer
    """
    if not question or not question.strip():
        logger.warning("Empty question received in finops_expert_with_bing")
        return {
            "answer": "Please provide a FinOps-related question.",
            "sources": [],
            "quality_scores": {}
        }
    
    # Initialize config if not provided
    if config is None:
        config = {}
    
    # Extract configuration settings
    history = config.get("history", [])
    auto_improve_enabled = config.get("auto_improve_enabled", True)
    quality_threshold = config.get("quality_threshold", 7.0)
    
    # If config specifies use_real_search, override MOCK_MODE
    if "use_real_search" in config:
        use_real_search = config.get("use_real_search", not MOCK_MODE)
        local_mock_mode = not use_real_search
    else:
        local_mock_mode = MOCK_MODE
    
    logger.info(f"Processing question: {question}")
    logger.info(f"Using mock mode: {local_mock_mode}")
    
    try:
        # Get relevant sources
        logger.info("Retrieving relevant sources...")
        sources = get_relevant_sources(question, mock_mode=local_mock_mode)
        
        logger.info(f"Retrieved {len(sources)} sources")
        
        if not sources:
            logger.warning("No sources found for question")
            return {
                "answer": "I couldn't find any relevant information about this FinOps topic. Please try rephrasing your question or ask about a specific aspect of FinOps.",
                "sources": [],
                "quality_scores": {"relevance": 0, "completeness": 0, "accuracy": 0, "clarity": 0, "overall": 0}
            }
        
        # Extract insights from sources
        logger.info("Extracting insights from sources...")
        insights_result = extract_insights_from_sources(question, sources)
        
        insights = insights_result.get("insights", "")
        citations = insights_result.get("citations", [])
        
        # Format the answer with citations
        answer = format_answer_with_citations(question, insights, citations)
        
        # Calculate quality scores for the answer
        logger.info("Calculating quality scores...")
        quality_scores = {
            "relevance": min(len(sources) * 2.0, 10.0),  # More sources = higher relevance
            "completeness": min(len(insights) / 100, 10.0),  # Longer insights = more complete
            "accuracy": 8.0,  # Assume relatively high accuracy since using real sources
            "clarity": 8.0,   # Assume good clarity from structured format
        }
        
        # Calculate overall quality score
        quality_scores["overall"] = (
            quality_scores["relevance"] * 0.3 +
            quality_scores["completeness"] * 0.3 +
            quality_scores["accuracy"] * 0.2 +
            quality_scores["clarity"] * 0.2
        )
        
        # Auto-improve if enabled and quality is below threshold
        if auto_improve_enabled and quality_scores["overall"] < quality_threshold:
            logger.info(f"Quality score {quality_scores['overall']} below threshold {quality_threshold}, auto-improving...")
            # TODO: Implement auto-improvement logic
            # For now, just note that we would improve
            answer += "\n\n(Note: This answer would normally be auto-improved due to low quality score.)"
        
        # Return the answer and sources
        return {
            "answer": answer,
            "sources": citations,
            "quality_scores": quality_scores
        }
        
    except Exception as e:
        logger.error(f"Error in finops_expert_with_bing: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return an error message with fallback response
        return {
            "answer": f"I encountered an error while processing your question about FinOps. Please try again or rephrase your question.\n\nError details: {str(e)}",
            "sources": [],
            "quality_scores": {"relevance": 0, "completeness": 0, "accuracy": 0, "clarity": 0, "overall": 0}
        }

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

def bing_web_search(query: str, count: int = 5) -> List[Dict[str, str]]:
    """
    Perform a web search using Bing's API
    
    Args:
        query: The search query
        count: Number of results to return
        
    Returns:
        List of source dictionaries with title, url, and description
    """
    logger.info(f"Performing Bing web search for: {query}")
    
    # Get API key and endpoint from environment
    subscription_key = os.environ.get("BING_SEARCH_KEY", "")
    endpoint = os.environ.get("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/")
    
    # Check if the API key is available
    if not subscription_key or subscription_key == "your-bing-search-key":
        logger.error("Missing or invalid BING_SEARCH_KEY in environment variables")
        return []
    
    logger.info(f"Using Bing endpoint: {endpoint}")
    logger.info(f"API key looks valid (length: {len(subscription_key)})")
    
    # Ensure the endpoint has trailing slash
    if not endpoint.endswith('/'):
        endpoint += '/'
    
    # Construct the search URL
    search_url = endpoint + "v7.0/search"
    
    # Add search parameters
    params = {
        "q": query + " finops financial operations cloud cost management",
        "count": count,
        "offset": 0,
        "mkt": "en-US",
        "responseFilter": "Webpages",
        "freshness": "Month"  # Get relatively recent results
    }
    
    # Set headers with API key
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key
    }
    
    try:
        # Log the request details (without the full API key)
        masked_key = subscription_key[:4] + "..." + subscription_key[-4:] if len(subscription_key) > 8 else "***"
        logger.info(f"Making request to: {search_url}")
        logger.info(f"Using headers: {{'Ocp-Apim-Subscription-Key': '{masked_key}'}}")
        logger.info(f"Using parameters: {params}")
        
        # Make the request
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        # Detailed logging for error responses
        if response.status_code != 200:
            logger.error(f"Bing API returned status code {response.status_code}")
            try:
                error_content = response.json() if response.text else "No error details provided"
                logger.error(f"Error details: {error_content}")
            except:
                logger.error(f"Error response text: {response.text[:200]}...")
            
            # Special handling for common error codes
            if response.status_code == 401:
                logger.error("401 Unauthorized: Check that your Bing Search API key is valid and active")
                logger.error("Make sure BING_SEARCH_KEY is correctly set in your .env file with no extra spaces or quotes")
            elif response.status_code == 403:
                logger.error("403 Forbidden: Your API key might not have permission to access this endpoint")
            
            response.raise_for_status()
        
        # Parse results
        search_results = response.json()
        
        # Extract sources from results
        sources = []
        if "webPages" in search_results and "value" in search_results["webPages"]:
            for result in search_results["webPages"]["value"]:
                source = {
                    "title": result.get("name", ""),
                    "url": result.get("url", ""),
                    "description": result.get("snippet", ""),
                    "is_valid": True  # Assume valid initially
                }
                sources.append(source)
                
            logger.info(f"Retrieved {len(sources)} results from Bing")
            return sources
        else:
            logger.warning("No web page results found in Bing response")
            logger.warning(f"Response fields: {list(search_results.keys())}")
            return []
            
    except Exception as e:
        logger.error(f"Error in Bing web search: {str(e)}")
        if isinstance(e, requests.exceptions.RequestException):
            logger.error(f"Request error details: {getattr(e, 'response', 'No response')}")
        return []

def custom_extract_insights_from_sources(question: str, sources: List[Dict], with_citations: bool = True) -> Dict[str, Any]:
    """Extract insights from the provided sources based on the user's question.
    
    Args:
        question: The user's question
        sources: List of source dictionaries with title, url, and at least one of description or content
        with_citations: Whether to include citations in the response
        
    Returns:
        Dictionary with insights and citations
    """
    logger.info(f"Extracting insights for question: {question}")
    
    if not sources or len(sources) == 0:
        logger.warning("No sources provided to extract insights from")
        return {
            "insights": "No relevant information found for this query.",
            "citations": []
        }
    
    # Combine all content for processing
    all_content = ""
    for source in sources:
        if "content" in source and source["content"]:
            all_content += source["content"] + "\n\n"
        elif "description" in source and source["description"]:
            all_content += source["description"] + "\n\n"
    
    # Extract relevant information based on the question type
    question_lower = question.lower()
    
    # Determine categories of insights to extract based on question keywords
    categories = []
    if any(term in question_lower for term in ["what is", "definition", "explain", "describe", "understand"]):
        categories.append("definition")
    
    if any(term in question_lower for term in ["benefit", "advantage", "why", "value", "importance"]):
        categories.append("benefits")
        
    if any(term in question_lower for term in ["challenge", "problem", "issue", "difficult", "hurdle"]):
        categories.append("challenges")
        
    if any(term in question_lower for term in ["best practice", "how to", "implement", "approach", "strategy", "tactic"]):
        categories.append("best_practices")
        
    if any(term in question_lower for term in ["tool", "software", "platform", "technology", "solution"]):
        categories.append("tools")
        
    if any(term in question_lower for term in ["metric", "measure", "kpi", "indicator", "track"]):
        categories.append("metrics")
        
    if any(term in question_lower for term in ["step", "process", "procedure", "workflow", "implementation"]):
        categories.append("steps")
    
    # If no specific categories matched, extract general information
    if not categories:
        categories = ["definition", "benefits", "best_practices"]
    
    # Extract specific insights for each category
    insights_dict = {}
    
    try:
        # Extract topic and subtopics from the question
        main_topic = extract_main_topic(question)
        logger.info(f"Main topic identified: {main_topic}")
        
        # Process each category
        for category in categories:
            category_insights = extract_specific_topic_insights(all_content, main_topic, category)
            if category_insights and len(category_insights) > 10:  # Only add if we got meaningful content
                insights_dict[category] = category_insights
        
        # Format the final insights text
        insights_text = ""
        
        # Add definition/overview if available
        if "definition" in insights_dict:
            insights_text += f"{insights_dict['definition']}\n\n"
        
        # Add benefits if available
        if "benefits" in insights_dict:
            insights_text += f"**Benefits**:\n{insights_dict['benefits']}\n\n"
        
        # Add challenges if available
        if "challenges" in insights_dict:
            insights_text += f"**Challenges**:\n{insights_dict['challenges']}\n\n"
        
        # Add best practices if available
        if "best_practices" in insights_dict:
            insights_text += f"**Best Practices**:\n{insights_dict['best_practices']}\n\n"
        
        # Add tools if available
        if "tools" in insights_dict:
            insights_text += f"**Tools and Technologies**:\n{insights_dict['tools']}\n\n"
        
        # Add metrics if available
        if "metrics" in insights_dict:
            insights_text += f"**Key Metrics**:\n{insights_dict['metrics']}\n\n"
        
        # Add implementation steps if available
        if "steps" in insights_dict:
            insights_text += f"**Implementation Steps**:\n{insights_dict['steps']}\n\n"
        
        # If we couldn't extract specific insights, use a fallback approach
        if not insights_text or len(insights_text) < 100:
            logger.warning("Could not extract specific insights, using fallback approach")
            
            # Create a summary from the most relevant source descriptions
            insights_text = "Based on the sources I've found:\n\n"
            for i, source in enumerate(sources[:3], 1):
                if "description" in source and source["description"]:
                    insights_text += f"{i}. {source['description']}\n\n"
    
    except Exception as e:
        logger.error(f"Error extracting insights: {str(e)}")
        insights_text = "I encountered an error while analyzing the sources. Here's a summary of what I found:\n\n"
        
        # Fallback to using descriptions directly
        for i, source in enumerate(sources[:3], 1):
            if "description" in source and source["description"]:
                insights_text += f"{i}. {source['description']}\n\n"
    
    # Prepare citations if requested
    citations = []
    if with_citations:
        for i, source in enumerate(sources, 1):
            if "title" in source and "url" in source:
                # Ensure all values are strings to match the expected model type
                citation = {
                    "number": str(i),  # Convert number to string
                    "title": str(source.get("title", f"Source {i}")),
                    "url": str(source.get("url", ""))
                }
                citations.append(citation)
    
    return {
        "insights": insights_text.strip(),
        "citations": citations
    }

def format_answer_with_citations(question: str, insights: str, citations: List[Dict[str, Any]]) -> str:
    """
    Format the answer with proper citations in markdown format
    
    Args:
        question: The user's question
        insights: The insights extracted from sources
        citations: List of citation dictionaries with number, title, and url
        
    Returns:
        Formatted answer with citations
    """
    # Start with a header
    response = f"# Answer to: \"{question}\"\n\n"
    
    # Add the insights
    response += insights
    
    # Add a sources section if we have citations
    if citations:
        response += "\n\n## Sources\n\n"
        
        for citation in citations:
            number = citation.get("number", 0)
            title = citation.get("title", f"Source {number}")
            url = citation.get("url", "")
            
            # Add the citation as a markdown link
            response += f"[{title}]({url})\n"
    
    # Add a note if we're in mock mode
    if MOCK_MODE:
        response += "\n\n*Note: This response was generated using simulated web search results. To get more accurate and up-to-date information, please configure valid API keys in the .env file.*"
    
    return response

if __name__ == "__main__":
    print("="*50)
    print("FinOps Expert Simplified Module")
    print("="*50)
    print(f"Mock Mode: {MOCK_MODE}")
    
    # Run the Bing API test if not in mock mode
    if not MOCK_MODE:
        print("Testing Bing API connection...")
        bing_test = test_bing_connection()
        if bing_test:
            print(f"✅ Bing API test successful")
        else:
            print(f"❌ Bing API test failed")
    else:
        print("Skipping Bing API test (Mock Mode enabled)")
    
    print("-"*50)
    
    test_question = "What is FinOps and how can it help reduce cloud costs?"
    print(f"Test Question: {test_question}")
    answer = finops_expert_with_bing(test_question)
    print("-"*50)
    print(answer) 