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

import os
import requests
import re
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool

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
    
    def _create_tools(self) -> List:
        """
        Create enhanced tools for the AI to use.
        
        Returns:
            List of tool methods that can be used by the AI for verification
            tasks. These tools include web searches, data validation, and
            content verification capabilities.
        """
        return [
            self.verification_tools._authoritative_web_search_tool,
            self.verification_tools._verify_website_tool,
            self.verification_tools._verify_phone_tool,
            self.verification_tools._verify_email_tool,
            self.verification_tools._verify_address_tool,
            self.verification_tools._verify_location_tool,
            self.verification_tools._verify_organization_tool,
            self.verification_tools._discover_services_tool,
            self.verification_tools._extract_service_details_tool
        ]
    
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
        information extraction. It uses a simplified approach without complex
        agents for better reliability and consistency.
        
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
            # Enhanced prompt for comprehensive resource verification including service discovery
            prompt = ChatPromptTemplate.from_template("""
            You are an expert data verification specialist for a community resource directory. 
            Your primary focus is to verify and improve BASIC INFORMATION and DISCOVER SERVICES for community resources.
            
            Current Resource Data:
            {current_data}
            
            TASK: Focus on verifying and improving these areas:
            
            BASIC INFORMATION VERIFICATION:
            1. Name: Verify organization name and check for current/active status
            2. Address: Verify address format and validity
            3. Phone: Verify phone number format and suggest proper formatting
            4. Email: Verify email format
            5. Website: Verify website accessibility and proper URL format
            
            SERVICE DISCOVERY AND VERIFICATION:
            6. Services: Discover what services the organization actually offers
            7. Service Details: Extract eligibility requirements, hours, costs, and other details
            8. Service Types: Categorize discovered services into standard types
            9. Hours of Operation: Find current operating hours
            10. Eligibility Requirements: Extract eligibility criteria for services
            11. Cost Information: Find cost details for services
            12. Languages Available: Identify language support
            13. Populations Served: Determine target populations
            
            CRITICAL FORMAT REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:
            
            For ALL service information, you MUST use ONLY pipe-separated format. NO EXCEPTIONS.
            
            REQUIRED PIPE FORMAT (copy this exactly):
            hours|Monday-Friday 8:00 AM-4:30 PM
            eligibility|Services available to residents of the Red Bird River Valley area
            cost|Free medication and supplies for uninsured patients through pharmaceutical company programs
            population|Residents of Appalachian Kentucky, families, children, adults, seniors, uninsured individuals
            language|Primarily English
            service_types|Healthcare,Education,Food Assistance
            
            STRICT RULES:
            1. ALWAYS use the pipe symbol (|) to separate field name from value
            2. NEVER use line breaks, indentation, or other formatting
            3. NEVER add explanatory text, confidence levels, or metadata after the pipe
            4. NEVER use bullet points, dashes, or other formatting
            5. ALWAYS put the field name first, then pipe, then the value
            6. STOP immediately after providing the pipe-separated data
            7. DO NOT add any additional text, explanations, or formatting
            
            FORBIDDEN FORMATS (DO NOT USE):
            ❌ eligibility
              Services available to residents...
            ❌ - eligibility: Services available...
            ❌ **Eligibility**: Services available...
            ❌ 1. eligibility: Services available...
            
            ONLY USE THIS FORMAT:
            ✅ eligibility|Services available to residents of the Red Bird River Valley area
            
            INSTRUCTIONS:
            - First verify basic contact information
            - Then use the website to discover and verify services offered
            - Extract detailed service information including hours, eligibility, costs
            - Categorize services into standard service types
            - Provide confidence levels for each verification (High/Medium/Low)
            - Focus on accuracy and completeness of both contact and service information
            
            TOOLS AVAILABLE:
            - _discover_services_tool: Use this to crawl the organization's website and discover services
            - _extract_service_details_tool: Use this to get detailed information about specific services
            - _authoritative_web_search_tool: Use this for additional verification
            
            FINAL REMINDER: When you provide service information, you MUST use ONLY the pipe format shown above. 
            Do not use any other formatting, line breaks, or explanatory text. 
            Just provide the pipe-separated data and stop.
            
            MANDATORY OUTPUT FORMAT - COPY THIS EXACTLY:
            hours|Monday-Friday 8:00 AM-4:30 PM
            eligibility|Services available to residents of the Red Bird River Valley area
            cost|Free medication and supplies for uninsured patients through pharmaceutical company programs
            population|Residents of Appalachian Kentucky, families, children, adults, seniors, uninsured individuals
            language|Primarily English
            service_types|Healthcare,Education,Food Assistance
            
            Please provide your analysis in a clear, structured format with both basic information and service discovery results.
            """)
            
            # Create a simple chain without complex agents
            chain = prompt | self.llm | StrOutputParser()
            
            # Format current data for the prompt
            formatted_data = self._format_data_for_prompt(current_data)
            
            # Get AI response
            ai_response = chain.invoke({"current_data": formatted_data})
            
            # Parse the AI response
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
        
        # Convert confidence levels to scores for backward compatibility
        confidence_scores = {}
        for field, level in confidence_levels.items():
            if level == "High":
                confidence_scores[field] = 90.0
            elif level == "Medium":
                confidence_scores[field] = 75.0
            elif level == "Low":
                confidence_scores[field] = 60.0
            else:
                confidence_scores[field] = 50.0
        
        return verified_data, change_notes, confidence_scores
    
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
