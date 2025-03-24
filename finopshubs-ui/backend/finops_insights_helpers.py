"""
FinOps Insights Helper Functions
--------------------------------
Helper functions for extracting insights from search results about FinOps topics.
These functions process raw text from search results to extract meaningful insights.
"""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse
import os

def extract_insights_from_sources(sources: List[Dict[str, str]], question: str) -> List[str]:
    """
    Extract meaningful insights from source descriptions relevant to the question
    
    Parameters:
    -----------
    sources : List[Dict[str, str]]
        List of source dictionaries containing title, url, and description
    question : str
        The original user question to help focus the extraction
        
    Returns:
    --------
    List[str]
        List of extracted insights formatted as markdown
    """
    # Combine all source content for processing
    combined_content = ""
    source_texts = []
    source_urls = []
    
    # Process each source and extract relevant text
    for source in sources:
        title = source.get("title", "")
        description = source.get("description", "")
        url = source.get("url", "")
        source_urls.append(url)
        
        # Create meaningful text from source
        combined_text = f"{title}. {description}"
        source_texts.append(combined_text)
        combined_content += combined_text + " "
    
    # Extract the main topic from the question (e.g., "FOCUS" from "What is FOCUS?")
    question_lower = question.lower()
    main_topic = extract_main_topic(question)
    
    # Check if the question is about a specific topic that appears in the sources
    is_specific_topic = False
    if main_topic and main_topic.lower() != "finops":
        # Check if this topic appears in any of the source URLs or titles
        for source in sources:
            if main_topic.lower() in source.get("title", "").lower() or main_topic.lower() in source.get("url", "").lower():
                is_specific_topic = True
                break
    
    # For specific topics like FOCUS that aren't general FinOps questions
    if is_specific_topic:
        return extract_specific_topic_insights(main_topic, sources, source_texts, question)
    
    # For general FinOps questions, continue with the existing categorization approach
    # Categories and their related keywords
    categories = {
        "definition": ["what is", "define", "explain", "meaning of", "concept of", "definition"],
        "benefits": ["benefits", "advantages", "pros", "value", "importance", "why"],
        "challenges": ["challenges", "difficulties", "problems", "cons", "issues", "obstacles"],
        "best_practices": ["best practices", "how to", "tips", "guidelines", "recommendations", "implement", "strategy"],
        "tools": ["tools", "applications", "software", "solutions", "platforms", "products"],
        "metrics": ["metrics", "kpis", "indicators", "measurements", "key metrics", "measure"],
        "implementation": ["implement", "steps", "process", "approach", "methodology", "framework"]
    }
    
    # Determine which categories to focus on based on the question
    relevant_categories = []
    for category, keywords in categories.items():
        if any(keyword in question_lower for keyword in keywords):
            relevant_categories.append(category)
    
    # If no specific categories identified, use definition and best practices
    if not relevant_categories:
        relevant_categories = ["definition", "best_practices"]
    
    # Function to extract information for each category
    insights = []
    
    # Extract key FinOps concepts and terms for context
    finops_terms = extract_finops_terms(combined_content)
    
    # Extract insights for each relevant category
    for category in relevant_categories:
        if category == "definition":
            definition_insights = extract_definition_from_sources(source_texts, finops_terms)
            insights.extend(definition_insights)
        
        elif category == "benefits":
            benefit_insights = extract_benefits_from_sources(source_texts, finops_terms)
            insights.extend(benefit_insights)
            
        elif category == "challenges":
            challenge_insights = extract_challenges_from_sources(source_texts, finops_terms)
            insights.extend(challenge_insights)
            
        elif category == "best_practices":
            practice_insights = extract_best_practices_from_sources(source_texts, finops_terms)
            insights.extend(practice_insights)
            
        elif category == "tools":
            tool_insights = extract_tools_from_sources(source_texts, finops_terms)
            insights.extend(tool_insights)
            
        elif category == "metrics":
            metric_insights = extract_metrics_from_sources(source_texts, finops_terms)
            insights.extend(metric_insights)
            
        elif category == "implementation":
            implementation_insights = extract_implementation_from_sources(source_texts, finops_terms)
            insights.extend(implementation_insights)
    
    # If we extracted fewer than 4 insights, add general FinOps information
    if len(insights) < 4:
        general_insights = [
            f"**FinOps** involves bringing financial accountability to cloud spending through collaboration between finance, engineering, and business teams",
            f"Effective cloud cost management requires balancing speed, cost, and quality based on business needs",
            f"Cloud financial operations should focus on optimizing resources while maintaining operational excellence"
        ]
        
        # Only add general insights not already covered
        for insight in general_insights:
            if not any(i.lower() in insight.lower() or insight.lower() in i.lower() for i in insights):
                insights.append(insight)
    
    # Remove duplicates while preserving order
    unique_insights = []
    for insight in insights:
        normalized = insight.lower()
        if not any(normalized in i.lower() or i.lower() in normalized for i in unique_insights):
            unique_insights.append(insight)
    
    return unique_insights[:8]  # Return up to 8 insights

def extract_finops_terms(text):
    """Extract key FinOps terms from the text"""
    core_terms = [
        "finops", "financial operations", "cloud financial management", 
        "cloud cost management", "cost optimization", "cloud economics",
        "cloud spending", "cost governance", "cloud cost", "cost allocation",
        "tagging", "chargeback", "showback", "forecasting", "budget",
        "reserved instances", "savings plans", "spot instances", "rightsizing",
        "waste reduction", "accountability", "visibility"
    ]
    
    found_terms = []
    for term in core_terms:
        if term in text.lower():
            found_terms.append(term)
            
    return found_terms

def extract_definition_from_sources(source_texts, finops_terms):
    """Extract definitions from source texts"""
    definitions = []
    definition_patterns = [
        r"(?:finops|financial operations|cloud financial management|cloud cost management)(?:\s+is|\s+refers to|\s+means|\s+involves|\s+represents)(?:[^.!?]*[.!?])",
        r"definition of (?:finops|financial operations|cloud financial management|cloud cost management)(?:[^.!?]*[.!?])",
        r"(?:finops|financial operations|cloud financial management|cloud cost management)(?:[^.!?]*?)\bdefined as\b(?:[^.!?]*[.!?])"
    ]
    
    for source in source_texts:
        # Check for definition patterns
        for pattern in definition_patterns:
            matches = re.findall(pattern, source.lower())
            for match in matches:
                # Clean up and format the definition
                definition = match.strip().capitalize()
                # Enhance with bold formatting for key terms
                for term in finops_terms:
                    if term in definition.lower():
                        definition = definition.replace(term, f"**{term}**")
                
                definitions.append(definition)
    
    # If no definition found in patterns, look for sentences with key terms
    if not definitions:
        for source in source_texts:
            sentences = re.split(r'(?<=[.!?])\s+', source)
            for sentence in sentences:
                if any(f" {term} " in f" {sentence.lower()} " for term in ["finops", "financial operations", "cloud financial management", "finops toolkit", "microsoft finops toolkit"]):
                    if any(verb in sentence.lower() for verb in ["is", "refers to", "means", "involves", "represents", "entails", "encompasses"]):
                        # Clean and format
                        definition = sentence.strip().capitalize()
                        # Bold key terms
                        for term in finops_terms:
                            if term in definition.lower():
                                definition = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", definition, flags=re.IGNORECASE)
                        
                        definitions.append(definition)
    
    # If still no definitions, create one from the most relevant source
    if not definitions and source_texts:
        most_relevant = source_texts[0]  # First source is often most relevant
        definitions = ["**FinOps** is the practice of bringing financial accountability to cloud spending, enabling teams to make business trade-offs between speed, cost, and quality."]
        
    return definitions[:2]  # Return up to 2 definitions

def extract_benefits_from_sources(source_texts, finops_terms):
    """Extract benefits from source texts"""
    benefits = []
    benefit_indicators = ["benefit", "advantage", "value", "gain", "enable", "help", "improve", "enhance", "increase", "optimize", "reduce"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence discusses benefits
            if any(indicator in sentence_lower for indicator in benefit_indicators):
                # Check if it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format the benefit
                    benefit = sentence.strip()
                    
                    # If sentence is too long, try to shorten it
                    if len(benefit) > 150:
                        parts = re.split(r',|\band\b|\bwhile\b|\bas\b|\bwhich\b', benefit)
                        if len(parts) > 1:
                            # Take the most relevant part containing benefit indicator and finops term
                            for part in parts:
                                part_lower = part.lower()
                                if any(indicator in part_lower for indicator in benefit_indicators) and any(term in part_lower for term in finops_terms):
                                    benefit = part.strip()
                                    break
                    
                    # Bold key terms and make sure it starts with a capital letter
                    benefit = benefit[0].upper() + benefit[1:]
                    for term in finops_terms:
                        if term in benefit.lower():
                            benefit = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", benefit, flags=re.IGNORECASE)
                    
                    # Add benefit if it's not too similar to existing ones
                    if not any(benefit.lower() in b.lower() or b.lower() in benefit.lower() for b in benefits):
                        benefits.append(benefit)
    
    # If no benefits found, provide default
    if not benefits:
        benefits = [
            "**Cost Visibility** enables teams to see and understand their cloud spending patterns",
            "**Financial Accountability** helps organizations make more informed decisions about cloud resource usage"
        ]
        
    return benefits[:3]  # Return up to 3 benefits

def extract_best_practices_from_sources(source_texts, finops_terms):
    """Extract best practices from source texts"""
    practices = []
    practice_indicators = ["practice", "recommend", "should", "best", "effective", "strategy", "approach", "implement", "establish", "develop", "create", "ensure"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence discusses practices
            if any(indicator in sentence_lower for indicator in practice_indicators):
                # Ensure it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format
                    practice = sentence.strip()
                    
                    # Format as action item if it's not already
                    if not any(practice.startswith(word) for word in ["Implement", "Establish", "Develop", "Create", "Ensure", "Set", "Use", "Deploy", "Build", "Enable"]):
                        # Try to convert to action format
                        for verb in ["implement", "establish", "develop", "create", "ensure", "set", "use", "deploy", "build", "enable"]:
                            if verb in sentence_lower:
                                # Find position of verb and restructure
                                verb_pos = sentence_lower.find(verb)
                                if verb_pos > 0 and verb_pos < len(sentence) // 2:  # Only if verb is in first half
                                    # Extract from verb position
                                    practice = sentence[verb_pos:].strip()
                                    # Capitalize first letter
                                    practice = practice[0].upper() + practice[1:]
                                    break
                    
                    # Bold key terms
                    for term in finops_terms:
                        if term in practice.lower():
                            practice = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", practice, flags=re.IGNORECASE)
                    
                    # Ensure it starts with capital letter
                    practice = practice[0].upper() + practice[1:]
                    
                    # Add if not too similar to existing ones
                    if not any(practice.lower() in p.lower() or p.lower() in practice.lower() for p in practices):
                        practices.append(practice)
    
    # If no practices found, provide default
    if not practices:
        practices = [
            "**Implement** tagging standards to track and allocate costs to business units",
            "**Establish** regular cost reviews to identify optimization opportunities"
        ]
        
    return practices[:3]  # Return up to 3 practices

def extract_challenges_from_sources(source_texts, finops_terms):
    """Extract challenges from source texts"""
    challenges = []
    challenge_indicators = ["challenge", "difficult", "problem", "issue", "obstacle", "struggle", "complex", "hard", "tough", "risk"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence discusses challenges
            if any(indicator in sentence_lower for indicator in challenge_indicators):
                # Ensure it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format
                    challenge = sentence.strip()
                    
                    # Bold key terms
                    for term in finops_terms:
                        if term in challenge.lower():
                            challenge = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", challenge, flags=re.IGNORECASE)
                    
                    # Ensure it starts with capital letter
                    challenge = challenge[0].upper() + challenge[1:]
                    
                    # Add if not too similar to existing ones
                    if not any(challenge.lower() in c.lower() or c.lower() in challenge.lower() for c in challenges):
                        challenges.append(challenge)
    
    # If no challenges found, provide default
    if not challenges:
        challenges = [
            "**Cost Visibility** across multiple cloud providers and services remains a significant challenge",
            "Maintaining compliance with budget constraints while ensuring performance can be difficult"
        ]
        
    return challenges[:2]  # Return up to 2 challenges

def extract_tools_from_sources(source_texts, finops_terms):
    """Extract tools and platforms mentioned in source texts"""
    tools = []
    tool_indicators = ["tool", "platform", "solution", "software", "application", "product", "service"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence mentions tools
            if any(indicator in sentence_lower for indicator in tool_indicators):
                # Ensure it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format
                    tool_info = sentence.strip()
                    
                    # Bold key terms
                    for term in finops_terms:
                        if term in tool_info.lower():
                            tool_info = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", tool_info, flags=re.IGNORECASE)
                    
                    # Also bold tool names
                    for indicator in tool_indicators:
                        if indicator in tool_info.lower():
                            tool_info = re.sub(rf'\b{re.escape(indicator)}\b', f"**{indicator}**", tool_info, flags=re.IGNORECASE)
                    
                    # Add if not too similar to existing ones
                    if not any(tool_info.lower() in t.lower() or t.lower() in tool_info.lower() for t in tools):
                        tools.append(tool_info)
    
    # If no tools found but "toolkit" in content, add info about Microsoft FinOps Toolkit
    if not tools and any("toolkit" in source.lower() for source in source_texts):
        tools = [
            "The **Microsoft FinOps Toolkit** provides resources and tools to help organizations implement FinOps practices in Azure"
        ]
        
    return tools[:2]  # Return up to 2 tool mentions

def extract_metrics_from_sources(source_texts, finops_terms):
    """Extract metrics and KPIs mentioned in source texts"""
    metrics = []
    metric_indicators = ["metric", "kpi", "measure", "indicator", "benchmark", "score", "ratio", "rate", "percentage"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence mentions metrics
            if any(indicator in sentence_lower for indicator in metric_indicators):
                # Ensure it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format
                    metric_info = sentence.strip()
                    
                    # Bold key terms
                    for term in finops_terms:
                        if term in metric_info.lower():
                            metric_info = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", metric_info, flags=re.IGNORECASE)
                    
                    # Also bold metric terms
                    for indicator in metric_indicators:
                        if indicator in metric_info.lower():
                            metric_info = re.sub(rf'\b{re.escape(indicator)}\b', f"**{indicator}**", metric_info, flags=re.IGNORECASE)
                    
                    # Add if not too similar to existing ones
                    if not any(metric_info.lower() in m.lower() or m.lower() in metric_info.lower() for m in metrics):
                        metrics.append(metric_info)
    
    return metrics[:2]  # Return up to 2 metric mentions

def extract_implementation_from_sources(source_texts, finops_terms):
    """Extract implementation steps or approaches from source texts"""
    implementations = []
    implementation_indicators = ["step", "process", "approach", "methodology", "framework", "implement", "adopt", "deploy", "establish", "use", "build", "enable"]
    
    for source in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', source)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence discusses implementation
            if any(indicator in sentence_lower for indicator in implementation_indicators):
                # Ensure it's related to FinOps
                if any(term in sentence_lower for term in finops_terms):
                    # Clean and format
                    implementation = sentence.strip()
                    
                    # Bold key terms
                    for term in finops_terms:
                        if term in implementation.lower():
                            implementation = re.sub(rf'\b{re.escape(term)}\b', f"**{term}**", implementation, flags=re.IGNORECASE)
                    
                    # Add if not too similar to existing ones
                    if not any(implementation.lower() in i.lower() or i.lower() in implementation.lower() for i in implementations):
                        implementations.append(implementation)
    
    return implementations[:2]  # Return up to 2 implementation notes

# Simple placeholder functions for backward compatibility
def extract_definition(text_blocks):
    """Extract definitions from text blocks (legacy function)"""
    return extract_definition_from_sources(text_blocks, [])

def extract_benefits(text_blocks):
    """Extract benefits from text blocks (legacy function)"""
    return extract_benefits_from_sources(text_blocks, [])

def extract_best_practices(text_blocks):
    """Extract best practices from text blocks (legacy function)"""
    return extract_best_practices_from_sources(text_blocks, [])

def extract_challenges(text_blocks):
    """Extract challenges from text blocks (legacy function)"""
    return extract_challenges_from_sources(text_blocks, [])

def extract_main_topic(question: str) -> str:
    """Extract the main topic from a question"""
    # For "what is X" questions
    what_is_match = re.search(r"what\s+is\s+([a-zA-Z0-9_\-]+)(\?|$|\s)", question.lower())
    if what_is_match:
        return what_is_match.group(1).upper()
    
    # For "tell me about X" questions
    tell_about_match = re.search(r"tell\s+(?:me\s+)?about\s+([a-zA-Z0-9_\-]+)(\?|$|\s)", question.lower())
    if tell_about_match:
        return tell_about_match.group(1).upper()
    
    # For "explain X" questions
    explain_match = re.search(r"explain\s+([a-zA-Z0-9_\-]+)(\?|$|\s)", question.lower())
    if explain_match:
        return explain_match.group(1).upper()
    
    # For "describe X" questions
    describe_match = re.search(r"describe\s+([a-zA-Z0-9_\-]+)(\?|$|\s)", question.lower())
    if describe_match:
        return describe_match.group(1).upper()
    
    # For specific format "X meaning" or "meaning of X"
    meaning_match = re.search(r"(?:meaning\s+of\s+|definition\s+of\s+)([a-zA-Z0-9_\-]+)(\?|$|\s)|([a-zA-Z0-9_\-]+)\s+meaning", question.lower())
    if meaning_match:
        # Check which group matched
        for group_idx in range(1, 4):
            if meaning_match.group(group_idx):
                return meaning_match.group(group_idx).upper()
    
    # For questions with the topic at the beginning
    topic_match = re.match(r"^([a-zA-Z0-9_\-]+)\s+", question)
    if topic_match:
        return topic_match.group(1).upper()
    
    # If we can't identify a specific pattern, return empty string
    return ""

def extract_specific_topic_insights(topic: str, sources: List[Dict[str, str]], source_texts: List[str], question: str) -> List[str]:
    """Extract insights specific to a particular topic rather than generic FinOps information"""
    insights = []
    
    # Check if any source title or URL contains the topic
    relevant_sources = []
    for i, source in enumerate(sources):
        title = source.get("title", "").lower()
        url = source.get("url", "").lower()
        if topic.lower() in title or topic.lower() in url:
            relevant_sources.append((i, source))
    
    # If we found relevant sources, focus on those
    if relevant_sources:
        # Extract title-based insights
        for idx, source in relevant_sources:
            title = source.get("title", "")
            # If the title contains information about what the topic is
            if "schema" in title.lower() and topic.lower() in title.lower():
                insights.append(f"**{topic}** appears to be a schema or data format used in {extract_context_from_title(title, topic)}")
            
            # If title contains toolkit, app, or service
            if any(term in title.lower() for term in ["toolkit", "app", "service", "platform", "framework", "tool", "solution"]):
                for term in ["toolkit", "app", "service", "platform", "framework", "tool", "solution"]:
                    if term in title.lower():
                        insights.append(f"**{topic}** is a {term} related to {extract_context_from_title(title, topic)}")
                        break
            
            # Extract from URL path components
            url = source.get("url", "")
            url_path = urlparse(url).path if url else ""
            path_components = [p for p in url_path.split("/") if p]
            
            # Look at the section of the documentation it's in
            if len(path_components) >= 2:
                section = path_components[0]
                subsection = path_components[1]
                if section and subsection:
                    insights.append(f"**{topic}** is related to {section.replace('-', ' ')} in the context of {subsection.replace('-', ' ')}")
            
            # If the URL is from Microsoft Learn, extract the documentation section
            if "learn.microsoft.com" in url:
                ms_sections = [p for p in url_path.split("/") if p and p not in ["en-us", "docs"]]
                if len(ms_sections) >= 2:
                    insights.append(f"**{topic}** is documented in the Microsoft {ms_sections[0].replace('-', ' ')} documentation, specifically in the {ms_sections[1].replace('-', ' ')} section")
    
    # Extract from source text
    for text in source_texts:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            # If the sentence directly mentions the topic
            if topic.lower() in sentence.lower():
                # Clean and format the sentence
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:  # Ensure it's a meaningful sentence
                    # Bold the topic
                    formatted_sentence = re.sub(
                        rf'\b{re.escape(topic)}\b', 
                        f"**{topic}**", 
                        clean_sentence, 
                        flags=re.IGNORECASE
                    )
                    insights.append(formatted_sentence)
    
    # If we still don't have insights, create some from the URL patterns
    if not insights:
        for source in sources:
            url = source.get("url", "")
            url_path = urlparse(url).path if url else ""
            filename = os.path.basename(url_path)
            
            if topic.lower() in filename.lower():
                insights.append(f"**{topic}** is documented at {url}, which appears to be related to {extract_context_from_path(url_path)}")
                
            if "schema" in url_path.lower() and topic.lower() in url_path.lower():
                insights.append(f"**{topic}** appears to be a data schema defined in {extract_context_from_path(url_path)}")
    
    # If we still don't have insights, provide a generic insight based on the sources
    if not insights:
        # Use the first source as reference since it's typically most relevant
        most_relevant_source = sources[0] if sources else None
        if most_relevant_source:
            title = most_relevant_source.get("title", "")
            url = most_relevant_source.get("url", "")
            insights.append(f"**{topic}** is referenced in \"{title}\", which suggests it may be related to {extract_context_from_title(title, topic)}")
            
            # Add a generic placeholder with source reference
            insights.append(f"Further information about **{topic}** can be found at the referenced link: {url}")
    
    return insights[:8]  # Return up to 8 insights

def extract_context_from_title(title: str, topic: str) -> str:
    """Extract context information from a title, removing the topic itself"""
    # Replace the topic in the title
    context = re.sub(rf'\b{re.escape(topic)}\b', '', title, flags=re.IGNORECASE).strip()
    # Remove any dash or colon at the beginning
    context = re.sub(r'^[-:\s]+', '', context).strip()
    return context

def extract_context_from_path(path: str) -> str:
    """Extract context information from a URL path"""
    # Split path into components
    components = [p for p in path.split("/") if p]
    
    # If we have at least 2 components, use them to create context
    if len(components) >= 2:
        return f"{components[0].replace('-', ' ')} {components[1].replace('-', ' ')}"
    
    # If only one component, use it
    elif len(components) == 1:
        return components[0].replace('-', ' ')
    
    # Fallback
    return "related documentation" 