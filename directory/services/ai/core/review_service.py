"""
AI Review Service for Resource Data Verification

This module provides the main AIReviewService class that orchestrates AI-powered
verification and improvement suggestions for resource data. The service uses
LangChain with the best free model from OpenRouter and integrates multiple
specialized modules through composition.

Architecture:
    - Main service orchestrates all verification activities
    - Uses composition pattern to integrate specialized modules
    - Maintains backward compatibility with existing API
    - Provides robust fallback mechanisms for error handling

Modules:
    - ai_verification_tools: Contains all @tool decorated verification methods
    - ai_web_scraper: Handles web page browsing and content extraction
    - ai_response_parser: Processes AI responses and extracts structured data
    - ai_report_generator: Creates comprehensive verification reports
    - ai_utilities: Provides utility functions and database integration

Dependencies:
    - langchain_openai: For LLM integration
    - langchain_core: For prompts and output parsing
    - dotenv: For environment variable management
    - requests: For HTTP requests
    - re: For regular expressions

Example:
    >>> service = AIReviewService()
    >>> result = service.verify_resource_data(resource_data)
    >>> print(result['verification_report'])
"""

import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# Import the new tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_pull_md import PullMdLoader

from directory.models import Resource
from directory.services.ai.core.base import BaseAIService

# Import the new Pydantic models for structured output
from ..models.verification_output import (
    AIVerificationOutput, calculate_confidence_score, calculate_confidence_level, parse_ai_verification_response
)

# Set up logging
logger = logging.getLogger(__name__)

# Import the new verification tools module
from ..tools.verification import VerificationTools
# Import the new web scraper module
from ..tools.web_scraper import WebScraper
# Import the new response parser module
from ..tools.response_parser import ResponseParser
# Import the new report generator module
from ..reports.generator import ReportGenerator
# Import the new utilities module
from ..utils.helpers import AIUtilities

# Constants
MAX_TOKENS = 4000
REQUEST_TIMEOUT = 15

# Load environment variables
load_dotenv()


class AIReviewService:
    """
    Enhanced service for AI-powered review and verification of resource data.
    
    This class serves as the main interface for AI verification services,
    orchestrating multiple specialized modules through composition. It maintains
    backward compatibility while providing enhanced functionality through
    modular architecture.
    
    The service uses the best free model from OpenRouter (meta-llama/llama-4-maverick:free)
    for optimal performance and cost-effectiveness. It integrates authoritative
    web searches and comprehensive verification tools to provide accurate
    resource data validation.
    
    Attributes:
        llm: The language model instance for AI processing
        verification_tools: Instance of VerificationTools for data validation
        web_scraper: Instance of WebScraper for web content extraction
        response_parser: Instance of ResponseParser for AI response processing
        report_generator: Instance of ReportGenerator for report creation
        utilities: Instance of AIUtilities for utility functions
        tools: List of available verification tools
        
    Example:
        >>> service = AIReviewService()
        >>> if service.is_available():
        ...     result = service.verify_resource_data({
        ...         'name': 'Example Organization',
        ...         'website': 'https://example.org',
        ...         'phone': '555-123-4567'
        ...     })
        ...     print(result['verification_report'])
    """
    
    def __init__(self):
        """
        Initialize the AI review service with all required components.
        
        Sets up the language model, initializes all specialized modules
        through composition, and creates the tool list for AI verification.
        The service uses the best free model from OpenRouter for optimal
        performance and cost-effectiveness.
        """
        self.llm = None
        self._initialize_llm()
        
        # Initialize verification tools using composition
        self.verification_tools = VerificationTools()
        # Initialize web scraper using composition
        self.web_scraper = WebScraper()
        # Initialize response parser using composition
        self.response_parser = ResponseParser()
        # Initialize report generator using composition
        self.report_generator = ReportGenerator()
        # Initialize utilities using composition
        self.utilities = AIUtilities()
        self.tools = self._create_tools()
    
    def _create_tools(self) -> List[BaseTool]:
        """
        Create tools for the AI to use.
        
        Returns:
            List of tools for web search, content extraction, and verification
        """
        tools = []
        
        # DuckDuckGo Search Tool - for finding resource information online
        search_tool = DuckDuckGoSearchRun(
            name="web_search",
            description="Search the web for information about community resources, organizations, and services. Use this to find current information about resource names, addresses, phone numbers, websites, and services offered."
        )
        tools.append(search_tool)
        
        # PullMdLoader Tool - for extracting content from web pages
        def fetch_webpage_content(url: str) -> str:
            """
            Fetch and convert a webpage to markdown format.
            
            Args:
                url: The URL of the webpage to fetch
                
            Returns:
                The webpage content in markdown format
            """
            try:
                loader = PullMdLoader(url=url)
                documents = loader.load()
                if documents:
                    return documents[0].page_content
                else:
                    return "No content found on the webpage."
            except Exception as e:
                logger.error(f"Error fetching webpage {url}: {str(e)}")
                return f"Error fetching webpage: {str(e)}"
        
        from langchain_core.tools import tool
        
        @tool
        def fetch_webpage_tool(url: str) -> str:
            """
            Fetch and convert a webpage to markdown format for analysis.
            
            Args:
                url: The URL of the webpage to fetch and convert
                
            Returns:
                The webpage content in markdown format
            """
            return fetch_webpage_content(url)
        
        tools.append(fetch_webpage_tool)
        
        # Add verification tools from VerificationTools class
        verification_tools_list = self.verification_tools._create_tools()
        tools.extend(verification_tools_list)
        
        return tools
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """
        Create a focused, executable prompt for systematic field verification.
        
        This streamlined prompt focuses on:
        - Clear execution instructions
        - Tool usage requirements
        - Structured output format
        - Practical verification approach
        """
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert data verification specialist. Your mission is to verify resource information using web searches and website content extraction.

## EXECUTION REQUIREMENTS
1. **USE THE TOOLS**: You MUST use web_search and fetch_webpage_tool to perform actual verification
2. **COMPLETE THE PROCESS**: Don't just plan - execute the verification
3. **STRUCTURED OUTPUT**: Return the complete JSON structure below

## VERIFICATION PROCESS
1. **Search for the organization**: Use web_search with "[organization name] [location]"
2. **Extract website content**: Use fetch_webpage_tool on the official website
3. **Verify all fields**: Check each field against found information
4. **Discover service areas**: Use _validate_service_area_tool to identify and validate geographic service areas
5. **Provide confidence scores**: 95-100% (official website), 85-94% (authoritative), 70-84% (verified), 50-69% (supporting), <50% (unreliable)

## REQUIRED OUTPUT FORMAT
Return ONLY a valid JSON object with this exact structure:

{{
  "resource_name": "Name of the resource",
  "verification_timestamp": "Current timestamp",
  "ai_model_used": "meta-llama/llama-4-maverick:free",
  "basic_information": {{
    "name": {{
      "field_name": "name",
      "original_value": "Original value",
      "verified_value": "Verified/updated value",
      "confidence_level": "VERY_HIGH|HIGH|MEDIUM|LOW|VERY_LOW",
      "confidence_score": 95.0,
      "status": "VERIFIED|UPDATED|CONFLICTING|NOT_FOUND",
      "sources": ["https://example.org"],
      "reasoning": "Explanation of verification",
      "change_notes": "Notes about changes",
      "missing_field_recommendations": "Recommendations if NOT_FOUND"
    }},
    "description": {{ /* same structure */ }},
    "category": {{ /* same structure */ }},
    "service_types": {{ /* same structure */ }}
  }},
  "contact_information": {{
    "phone": {{ /* same structure */ }},
    "email": {{ /* same structure */ }},
    "website": {{ /* same structure */ }}
  }},
  "address_information": {{
    "address1": {{ /* same structure */ }},
    "address2": {{ /* same structure */ }},
    "city": {{ /* same structure */ }},
    "state": {{ /* same structure */ }},
    "county": {{ /* same structure */ }},
    "postal_code": {{ /* same structure */ }}
  }},
  "service_information": {{
    "hours_of_operation": {{ /* same structure */ }},
    "is_emergency_service": {{ /* same structure */ }},
    "is_24_hour_service": {{ /* same structure */ }},
    "eligibility_requirements": {{ /* same structure */ }},
    "populations_served": {{ /* same structure */ }},
    "insurance_accepted": {{ /* same structure */ }},
    "cost_information": {{ /* same structure */ }},
    "languages_available": {{ /* same structure */ }},
    "capacity": {{ /* same structure */ }}
  }},
  "service_areas": {{
    "discovered_areas": [
      {{
        "area_name": "Laurel County, KY",
        "area_type": "COUNTY",
        "validation_status": "VALID|INVALID|UNKNOWN",
        "confidence_score": 95.0,
        "geographic_scope": "in_scope|out_of_scope|unknown",
        "source": "website_content|description|manual_discovery",
        "validation_message": "Exact match found: Laurel County (COUNTY)"
      }}
    ],
    "current_areas": [
      {{
        "area_name": "Current area name",
        "area_type": "Current area type",
        "validation_status": "VALID|INVALID|UNKNOWN"
      }}
    ],
    "recommendations": [
      {{
        "action": "ADD|REMOVE|UPDATE",
        "area_name": "Area name",
        "reason": "Reason for recommendation",
        "confidence": 95.0
      }}
    ]
  }},
  "source_information": {{
    "source": {{ /* same structure */ }},
    "notes": {{ /* same structure */ }}
  }},
  "summary": {{
    "total_fields_processed": 23,
    "verified_fields_count": 18,
    "updated_fields_count": 3,
    "conflicting_fields_count": 1,
    "not_found_fields_count": 1,
    "average_confidence_score": 87.5,
    "overall_verification_status": "VERIFIED|PARTIALLY_VERIFIED|NEEDS_REVIEW|NOT_FOUND"
  }},
  "sources_used": [
    {{
      "url": "https://example.org",
      "type": "official_website",
      "reliability": "VERY_HIGH"
    }}
  ],
  "verification_notes": "General notes about the verification process"
}}

## SERVICE AREA DISCOVERY REQUIREMENTS
1. **DISCOVER SERVICE AREAS**: Analyze website content and descriptions to identify geographic service areas
2. **VALIDATE AREAS**: Use _validate_service_area_tool to check if discovered areas exist in the database
3. **GEOGRAPHIC CONSTRAINTS**: Focus on areas within the system's scope (primarily Kentucky and surrounding regions)
4. **AREA TYPES**: Look for cities, counties, states, and custom service areas
5. **VALIDATION PRIORITY**: Prioritize areas that are validated as "in_scope" and "VALID"

## CRITICAL INSTRUCTIONS
1. **START VERIFICATION NOW**: Begin with web_search for the organization
2. **EXTRACT WEBSITE CONTENT**: Use fetch_webpage_tool on the official website
3. **VERIFY EVERY FIELD**: Provide verification for all 23 fields
4. **DISCOVER SERVICE AREAS**: Use _validate_service_area_tool to identify and validate geographic coverage
5. **COMPLETE THE JSON**: Return the full structured output including service_areas section
6. **NO PLANNING**: Execute the verification, don't just plan it
7. **FINISH THE PROCESS**: Even if searches don't find relevant info, complete the JSON output
8. **USE AVAILABLE DATA**: If web searches fail, use the original data and mark confidence appropriately

## FIELD-SPECIFIC RULES
- **PHONE NUMBERS**: Only change if you find the EXACT same number in multiple sources OR if the original number is clearly wrong (e.g., wrong area code). If uncertain, keep the original.
- **WEBSITES**: If you can't access a website due to SSL errors or other technical issues, KEEP the original URL and mark as "unverified due to access issues" - don't clear the field.
- **ELIGIBILITY REQUIREMENTS**: Only add if explicitly stated on official sources, not inferred from general knowledge.
- **CONFIDENCE SCORES**: Use lower confidence (40-60%) for significant changes without strong verification.
- **SERVICE AREAS**: 
  - Discover areas from website content, descriptions, and organization information
  - Use _validate_service_area_tool to validate each discovered area
  - Include areas with validation_status "VALID" and geographic_scope "in_scope"
  - Prioritize counties, cities, and states over custom areas
  - Mark areas as "out_of_scope" if they're clearly outside Kentucky/surrounding regions

Remember: Your verification decisions impact vulnerable populations. Be thorough and decisive. COMPLETE THE FULL VERIFICATION PROCESS AND GENERATE THE COMPLETE JSON OUTPUT.

Remember: Your verification decisions impact vulnerable populations. Be thorough and decisive."""),
            ("human", "Please verify and improve this resource data: {input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    def _initialize_llm(self):
        """
        Initialize the language model with the best free model from OpenRouter.
        
        Uses meta-llama/llama-4-maverick:free which provides:
        - 128K context window (perfect for detailed resource data)
        - 17B parameters (good balance of capability and speed)
        - Multimodal capabilities
        - Latest model (April 2025)
        - High throughput for processing multiple resources
        - FREE tier available
        
        Raises:
            Exception: If the model initialization fails
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")
            return
        
        # Use the BEST free model for resource verification
        # meta-llama/llama-4-maverick:free is the optimal choice:
        # - 128K context (perfect for detailed resource data)
        # - 17B parameters (good balance of capability and speed)
        # - Multimodal capabilities
        # - Latest model (April 2025)
        # - High throughput for processing multiple resources
        # - FREE tier available
        best_model = "meta-llama/llama-4-maverick:free"
        
        try:
            logger.info(f"Initializing best free model: {best_model}")
            llm = ChatOpenAI(
                model=best_model,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1,  # Low temperature for consistent verification
                max_tokens=MAX_TOKENS
            )
            
            # Test the model with a simple query
            test_response = llm.invoke("Hello, can you respond with 'OK'?")
            if test_response and test_response.content:
                logger.info(f"Successfully initialized model: {best_model}")
                self.llm = llm
                self.current_model = best_model
                return
            else:
                logger.error(f"Model {best_model} returned empty response")
                
        except Exception as e:
            logger.error(f"Failed to initialize {best_model}: {str(e)}")
            logger.info("Falling back to manual verification mode")
        
        self.llm = None
    
    def verify_resource_data(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced verification of resource data with comprehensive validation.
        
        This method performs AI-powered verification of resource data including
        basic contact information, service discovery, and detailed service
        information extraction. It uses JSON output parsing for compatibility
        with all models, including those that don't support structured output.
        
        The verification process includes:
        - Basic information validation (name, address, phone, email, website)
        - Service discovery and categorization
        - Detailed service information extraction (hours, eligibility, costs)
        - Confidence scoring for all verifications
        - Comprehensive report generation
        
        Args:
            current_data: Dictionary containing the current resource data to verify.
                Expected keys include: name, address, phone, email, website, etc.
                
        Returns:
            Dictionary containing:
                - verified_data: Dict with verified and improved resource data
                - change_notes: Dict with notes about changes made
                - confidence_scores: Dict with confidence scores for each field
                - report: String with comprehensive verification report
                - ai_response: String with raw AI response for debugging
                - structured_output: AIVerificationOutput object with detailed results
                
        Raises:
            Exception: If AI verification fails, falls back to manual verification
            
        Example:
            >>> service = AIReviewService()
            >>> result = service.verify_resource_data({
            ...     'name': 'Example Org',
            ...     'website': 'https://example.org'
            ... })
            >>> print(result['verified_data']['name'])
            >>> print(result['confidence_scores']['name'])
        """
        # Store current resource data for web search tool
        self.current_resource_data = current_data
        self.verification_tools.set_resource_data(current_data)
        
        if not self.llm:
            return self._get_fallback_response(current_data)
        
        try:
            # Format current data for the prompt
            formatted_data = self._format_data_for_prompt(current_data)
            
            # Create agent with tools (without structured output)
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self._create_agent_prompt()
            )
            
            # Create agent executor
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,  # Increased from 5 to allow for comprehensive verification
                max_execution_time=120,  # 2 minutes to allow for web searches and content extraction
                early_stopping_method="generate"  # Generate final response when limits reached
            )
            
            # Get AI response
            result = agent_executor.invoke({
                "input": f"Please verify and improve this resource data: {formatted_data}"
            })
            
            # Extract AI response
            ai_response = str(result.get("output", ""))
            
            # Try to parse structured output from the response using enhanced parser
            try:
                # Use the new enhanced parser that handles mixed data types
                verification_output = parse_ai_verification_response(ai_response)
                
                if verification_output:
                    # Generate verification report
                    report = self._generate_verification_report_from_structured_output(
                        current_data, verification_output
                    )
                    
                    # Convert verified_data to string format for backward compatibility
                    verified_data_strings = {}
                    for field_name, value in verification_output.verified_data.items():
                        if isinstance(value, list):
                            verified_data_strings[field_name] = ", ".join(str(item) for item in value)
                        elif isinstance(value, bool):
                            verified_data_strings[field_name] = str(value).lower()
                        elif value is None:
                            verified_data_strings[field_name] = ""
                        else:
                            verified_data_strings[field_name] = str(value)
                    
                    # Create change notes from verification statuses
                    change_notes = {}
                    for field_name, status in verification_output.verification_statuses.items():
                        if status in ['UPDATED', 'CONFLICTING']:
                            change_notes[field_name] = f"Field {status.lower()} during verification"
                    
                    return {
                        'verified_data': verified_data_strings,
                        'change_notes': change_notes,
                        'confidence_scores': verification_output.confidence_scores,
                        'report': report,
                        'ai_response': ai_response,
                        'structured_output': verification_output
                    }
                else:
                    raise Exception("Failed to parse AI response")
                        
            except Exception as parse_error:
                logger.warning(f"Failed to parse structured output: {parse_error}")
                # Fallback to old parsing method
                verified_data, change_notes, confidence_scores = self._parse_ai_response(ai_response, current_data)
                
                # Generate verification report
                report = self._generate_verification_report(current_data, verified_data, change_notes, confidence_scores)
                
                return {
                    'verified_data': verified_data,
                    'change_notes': change_notes,
                    'confidence_scores': confidence_scores,
                    'report': report,
                    'ai_response': ai_response
                }
            
        except Exception as e:
            logger.error(f"Error in AI verification: {str(e)}")
            return self._get_fallback_response(current_data)
    
    def _handle_website_access_issues(self, url: str, error: str) -> str:
        """
        Handle website access issues and provide guidance for the AI.
        
        Args:
            url: The URL that couldn't be accessed
            error: The error message
            
        Returns:
            Guidance string for the AI
        """
        if "SSL" in error or "certificate" in error:
            return f"Website {url} exists but couldn't be accessed due to SSL certificate issues. Keep the original URL and mark as 'unverified due to technical access issues'."
        elif "timeout" in error or "connection" in error:
            return f"Website {url} couldn't be accessed due to connection issues. Keep the original URL and mark as 'unverified due to connection issues'."
        else:
            return f"Website {url} couldn't be accessed: {error}. Keep the original URL and mark as 'unverified due to access issues'."

    def _format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format resource data for the AI prompt.
        
        Converts a dictionary of resource data into a formatted string
        suitable for inclusion in AI prompts. Only includes non-empty
        values to reduce noise in the prompt.
        
        Args:
            data: Dictionary containing resource data with various keys
                (name, address, phone, email, website, etc.)
                
        Returns:
            Formatted string with key-value pairs, one per line
            
        Example:
            >>> data = {'name': 'Example Org', 'phone': '555-1234', 'email': ''}
            >>> formatted = service._format_data_for_prompt(data)
            >>> print(formatted)
            name: Example Org
            phone: 555-1234
        """
        formatted_lines = []
        for key, value in data.items():
            if value:  # Only include non-empty values
                formatted_lines.append(f"{key}: {value}")
        return "\n".join(formatted_lines)
    
    def _parse_ai_response(self, response: str, current_data: Dict[str, Any]) -> tuple:
        """
        Parse AI response and extract verified data, change notes, and confidence scores.
        
        Uses the response parser module to extract structured information from
        the AI response. Converts confidence levels to numerical scores for
        backward compatibility with existing systems.
        
        Args:
            response: Raw AI response string containing verification results
            current_data: Original resource data for comparison
                
        Returns:
            Tuple containing:
                - verified_data: Dict with verified and improved resource data
                - change_notes: Dict with notes about changes made
                - confidence_scores: Dict with numerical confidence scores (0-100)
                
        Note:
            Confidence levels are converted as follows:
            - "High" -> 90.0
            - "Medium" -> 75.0
            - "Low" -> 60.0
            - Unknown -> 50.0
        """
        # Use the response parser module for enhanced parsing
        parsed_result = self.response_parser._parse_ai_response(response, current_data)
        
        verified_data = parsed_result['verified_data']
        change_notes = parsed_result['change_notes']
        confidence_levels = parsed_result['confidence_levels']
        
        # Parse service areas from AI response
        service_areas_data = self._parse_service_areas_from_response(response, current_data)
        if service_areas_data:
            verified_data['service_areas'] = service_areas_data
        
        # Convert confidence levels to scores for backward compatibility
        confidence_scores = {}
        for field, level in confidence_levels.items():
            # Use the new confidence score calculation
            confidence_scores[field] = self.response_parser._calculate_confidence_score(level)
        
        return verified_data, change_notes, confidence_scores
    
    def _parse_service_areas_from_response(self, response: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse service area information from AI response.
        
        Extracts discovered areas, current areas, and recommendations from the
        AI response's service_areas section. Validates discovered areas and
        provides structured output for service area management.
        
        Args:
            response: Raw AI response string
            current_data: Original resource data containing current service areas
            
        Returns:
            Dictionary containing parsed service area data:
                - discovered_areas: List of newly discovered service areas
                - current_areas: List of existing service areas
                - recommendations: List of recommendations for service area changes
        """
        import json
        import re
        
        try:
            # Extract JSON from AI response with better error handling
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in AI response")
                return {}
                
            json_str = json_match.group(0)
            
            # Clean the JSON string to handle control characters and truncation
            json_str = self._clean_json_string(json_str)
            
            try:
                parsed_data = json.loads(json_str)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON decode error: {json_error}")
                # Try to extract just the service_areas section
                service_areas_match = re.search(r'"service_areas"\s*:\s*\{[^}]*\}', json_str, re.DOTALL)
                if service_areas_match:
                    service_areas_json = "{" + service_areas_match.group(0) + "}"
                    try:
                        parsed_data = json.loads(service_areas_json)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse service_areas section")
                        return {}
                else:
                    return {}
            
            # Extract service_areas section
            service_areas = parsed_data.get('service_areas', {})
            if not service_areas:
                # If we couldn't find service_areas in the main structure, 
                # the parsed_data might be the service_areas object itself
                if 'discovered_areas' in parsed_data or 'current_areas' in parsed_data:
                    service_areas = parsed_data
                else:
                    logger.warning("No service_areas section found in AI response")
                    return {}
            
            # Extract discovered areas
            discovered_areas = service_areas.get('discovered_areas', [])
            
            # Extract and validate current areas
            current_areas = service_areas.get('current_areas', [])
            validated_current_areas = []
            for area in current_areas:
                if isinstance(area, dict) and area.get('area_name'):
                    validated_current_areas.append(area)
                else:
                    logger.warning(f"Invalid current area format: {area}")
            current_areas = validated_current_areas
            
            # Extract and validate recommendations
            recommendations = service_areas.get('recommendations', [])
            validated_recommendations = []
            for rec in recommendations:
                if isinstance(rec, dict) and rec.get('action') and rec.get('area_name'):
                    validated_recommendations.append(rec)
                else:
                    logger.warning(f"Invalid recommendation format: {rec}")
            recommendations = validated_recommendations
            
            # Validate discovered areas using the service area validation tool
            validated_discovered_areas = []
            for area in discovered_areas:
                if isinstance(area, dict):
                    # Check if area is already validated by AI
                    validation_status = area.get('validation_status', 'UNKNOWN')
                    geographic_scope = area.get('geographic_scope', 'unknown')
                    
                    # Only include areas that are valid and in scope
                    if validation_status == 'VALID' and geographic_scope == 'in_scope':
                        validated_discovered_areas.append(area)
                    elif validation_status == 'VALID' and geographic_scope == 'unknown':
                        # If geographic scope is unknown but validation is valid, include with warning
                        area['geographic_scope'] = 'in_scope'  # Assume in scope if valid
                        validated_discovered_areas.append(area)
                    else:
                        # Log invalid areas for debugging
                        logger.info(f"Filtered out invalid service area: {area.get('area_name', 'Unknown')} - Status: {validation_status}, Scope: {geographic_scope}")
            
            return {
                'discovered_areas': validated_discovered_areas,
                'current_areas': current_areas,
                'recommendations': recommendations
            }
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Error parsing service areas from AI response: {str(e)}")
            return {}
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean JSON string to handle control characters and truncation issues.
        
        Args:
            json_str: Raw JSON string that may contain control characters
            
        Returns:
            Cleaned JSON string ready for parsing
        """
        import re
        
        # Remove control characters except newlines and tabs
        json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_str)
        
        # Handle truncated JSON by finding the last complete object
        brace_count = 0
        cleaned_str = ""
        
        for char in json_str:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            
            cleaned_str += char
            
            # If we've closed all braces, we have a complete JSON object
            if brace_count == 0:
                break
        
        # If we still have unclosed braces, try to close them
        if brace_count > 0:
            cleaned_str += '}' * brace_count
        
        return cleaned_str
    
    def _get_fallback_response(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide fallback response when AI model is not available.
        
        Returns a standardized response structure when the AI model cannot
        be initialized or is unavailable. This ensures the service remains
        functional even when AI capabilities are not available.
        
        Args:
            current_data: Original resource data to return unchanged
                
        Returns:
            Dictionary with fallback response structure:
                - verified_data: Copy of original data (no changes)
                - change_notes: Status message indicating fallback mode
                - confidence_scores: Low confidence score (50.0)
                - report: User-friendly message about service unavailability
                - ai_response: Debug message indicating fallback mode
        """
        return {
            'verified_data': current_data.copy(),
            'change_notes': {'status': 'AI model not available - using fallback verification'},
            'confidence_scores': {'overall': 50.0},
            'report': 'AI verification service is currently unavailable. Please try again later.',
            'ai_response': 'Fallback mode - AI model not available'
        }
    
    def _generate_verification_report(self, current_data: Dict[str, Any], verified_data: Dict[str, Any], 
                                    change_notes: Dict[str, str], confidence_scores: Dict[str, float]) -> str:
        """
        Generate a comprehensive verification report.
        
        Converts numerical confidence scores to confidence levels and uses
        the report generator module to create a detailed verification report
        with all findings, changes, and confidence assessments.
        
        Args:
            current_data: Original resource data before verification
            verified_data: Verified and improved resource data
            change_notes: Notes about changes made during verification
            confidence_scores: Numerical confidence scores (0-100) for each field
                
        Returns:
            Formatted markdown string containing the complete verification report
            
        Note:
            Confidence scores are converted to levels as follows:
            - 90+ -> "High"
            - 70-89 -> "Medium"
            - <70 -> "Low"
        """
        # Convert confidence scores to levels for the report generator
        confidence_levels = {}
        for field, score in confidence_scores.items():
            if score >= 90:
                confidence_levels[field] = "High"
            elif score >= 70:
                confidence_levels[field] = "Medium"
            else:
                confidence_levels[field] = "Low"
        
        # Use the report generator module for enhanced report generation
        return self.report_generator._generate_verification_report(
            current_data=current_data,
            verified_data=verified_data,
            change_notes=change_notes,
            confidence_levels=confidence_levels,
            verification_notes={},  # Empty for now, can be enhanced later
            ai_response=""  # Empty for now, can be enhanced later
        )
    
    def _generate_verification_report_from_structured_output(
        self, current_data: Dict[str, Any], structured_output: AIVerificationOutput
    ) -> str:
        """
        Generate verification report from structured output.
        
        Args:
            current_data: Original resource data
            structured_output: Structured verification output
            
        Returns:
            Formatted verification report
        """
        report_lines = []
        report_lines.append(f"AI Verification Report for: {structured_output.resource_name}")
        report_lines.append(f"Timestamp: {datetime.now().isoformat()}")
        report_lines.append("=" * 60)
        
        # Summary
        report_lines.append(f"Summary:")
        report_lines.append(f"  Resource: {structured_output.resource_name}")
        report_lines.append(f"  Fields Verified: {len(structured_output.verified_data)}")
        report_lines.append(f"  Sources Used: {len(structured_output.sources_used)}")
        report_lines.append("")
        
        # Field details - using the simplified structure
        report_lines.append("Field Verification Details:")
        report_lines.append("-" * 40)
        
        # Get all field verifications
        for verification in structured_output.get_all_field_verifications():
            field_name = verification["field_name"]
            verified_value = verification["verified_value"]
            confidence_score = verification["confidence_score"]
            sources = verification["sources"]
            
            # Only show fields that have some verification activity
            if verified_value or sources:
                report_lines.append(f"Field: {field_name}")
                if verified_value:
                    report_lines.append(f"  Verified: {verified_value}")
                report_lines.append(f"  Confidence: {confidence_score:.1f}%")
                if sources:
                    report_lines.append(f"  Sources: {', '.join(sources)}")
                report_lines.append("")
        
        # Sources used
        if structured_output.sources_used:
            report_lines.append("Sources Used:")
            for source in structured_output.sources_used:
                report_lines.append(f"  - {source}")
            report_lines.append("")
        
        # Verification notes
        if structured_output.verification_notes:
            report_lines.append("Verification Notes:")
            report_lines.append(structured_output.verification_notes)
        
        return "\n".join(report_lines)
    
    def is_available(self) -> bool:
        """
        Check if the AI service is available.
        
        Determines whether the AI language model has been successfully
        initialized and is ready to process verification requests.
        
        Returns:
            True if the AI service is available and ready for use,
            False if the model failed to initialize or is unavailable
            
        Example:
            >>> service = AIReviewService()
            >>> if service.is_available():
            ...     result = service.verify_resource_data(data)
            ... else:
            ...     print("AI service is not available")
        """
        return self.llm is not None
