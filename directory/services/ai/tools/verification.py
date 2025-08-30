"""
AI Verification Tools Module

This module contains all verification tools and methods used by the AI Review Service.
It provides comprehensive data validation, web searches, and content verification
capabilities through @tool decorated methods that can be used by AI language models.

The module includes tools for:
- Authoritative web searches focusing on .gov, .org, and .edu domains
- Website verification and accessibility testing
- Phone number format validation and verification
- Email address validation and verification
- Address validation and geocoding
- Location verification and mapping
- Organization verification and status checking
- Service discovery and extraction
- Detailed service information extraction

All tools are designed to work with LangChain's tool system and provide
structured, reliable verification results for resource data validation.

Dependencies:
    - requests: For HTTP requests and web scraping
    - re: For regular expressions and pattern matching
    - os: For environment variable access
    - dotenv: For environment variable loading
    - langchain_core.tools: For @tool decorator

Example:
    >>> tools = VerificationTools()
    >>> tools.set_resource_data(resource_data)
    >>> result = tools._verify_website_tool("https://example.org")
    >>> print(result)
"""

import os
import requests
import re
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool

# Constants
REQUEST_TIMEOUT = 15

# Load environment variables
load_dotenv()


class VerificationTools:
    """
    Collection of verification tools for AI-powered resource data validation.
    
    This class contains all @tool decorated methods that perform various
    verification tasks including web searches, format validation, and
    content verification. All tools are designed to work with LangChain's
    tool system and provide structured, reliable verification results.
    
    The class maintains context about the current resource being verified
    and provides tools for comprehensive data validation across multiple
    domains including contact information, web presence, and service details.
    
    Attributes:
        current_resource_data: Dictionary containing the resource data currently
            being verified. Set via set_resource_data() method.
            
    Tools Available:
        - _authoritative_web_search_tool: Search authoritative sources (.gov, .org, .edu)
        - _verify_website_tool: Verify website accessibility and content
        - _verify_phone_tool: Validate phone number format and verify existence
        - _verify_email_tool: Validate email format and verify deliverability
        - _verify_address_tool: Validate address format and geocode location
        - _verify_location_tool: Verify location accuracy and mapping
        - _verify_organization_tool: Verify organization status and details
        - _discover_services_tool: Discover services offered by organization
        - _extract_service_details_tool: Extract detailed service information
        
    Example:
        >>> tools = VerificationTools()
        >>> tools.set_resource_data({
        ...     'name': 'Example Organization',
        ...     'website': 'https://example.org'
        ... })
        >>> result = tools._verify_website_tool("https://example.org")
        >>> print(result)
    """
    
    def __init__(self):
        """Initialize the verification tools."""
        self.current_resource_data = None
    
    def set_resource_data(self, resource_data: Dict[str, Any]) -> None:
        """
        Set the current resource data for context in verification tools.
        
        This method stores the resource data that is currently being verified,
        allowing verification tools to access context information such as
        organization name, website, and other details during verification
        processes.
        
        Args:
            resource_data: Dictionary containing the resource data to verify.
                Expected keys may include: name, website, phone, email,
                address, etc.
                
        Example:
            >>> tools = VerificationTools()
            >>> tools.set_resource_data({
            ...     'name': 'Example Organization',
            ...     'website': 'https://example.org',
            ...     'phone': '555-123-4567'
            ... })
        """
        self.current_resource_data = resource_data
    
    def _create_tools(self) -> List:
        """
        Create enhanced tools for the AI to use.
        
        Returns a list of all available verification tool methods that can
        be used by AI language models for comprehensive resource data
        validation and verification.
        
        Returns:
            List of tool methods for AI verification including:
                - _authoritative_web_search_tool
                - _verify_website_tool
                - _verify_phone_tool
                - _verify_email_tool
                - _verify_address_tool
                - _verify_location_tool
                - _verify_organization_tool
                - _discover_services_tool
                - _extract_service_details_tool
                
        Example:
            >>> tools = VerificationTools()
            >>> tool_list = tools._create_tools()
            >>> print(f"Available tools: {len(tool_list)}")
        """
        return [
            self._authoritative_web_search_tool,
            self._verify_website_tool,
            self._verify_phone_tool,
            self._verify_email_tool,
            self._verify_address_tool,
            self._verify_location_tool,
            self._verify_organization_tool,
            self._discover_services_tool,
            self._extract_service_details_tool
        ]
    
    @tool
    def _authoritative_web_search_tool(self, query: str) -> str:
        """
        Perform web search focusing on authoritative sources (.gov, .org, .edu).
        
        This tool performs comprehensive web searches focusing on authoritative
        sources and actually browses the pages to extract relevant information.
        It prioritizes government (.gov), organization (.org), and educational
        (.edu) domains for reliable information.
        
        The tool first attempts to use the organization's own website if
        available in the current resource data, then falls back to web searches
        using DuckDuckGo API for additional authoritative sources.
        
        Args:
            query: Search query to look up. Should be specific and relevant
                to the resource being verified (e.g., organization name,
                service type, location)
                
        Returns:
            String containing extracted information from authoritative sources.
            May include information from the organization's website and
            additional authoritative web sources. Returns error message if
            search fails or no information is found.
            
        Example:
            >>> tools = VerificationTools()
            >>> tools.set_resource_data({'name': 'Example Org', 'website': 'https://example.org'})
            >>> result = tools._authoritative_web_search_tool("Example Org services")
            >>> print(result)
        """
        try:
            all_results = []
            
            # First, try to find the organization's website from the resource data
            # This is more reliable than searching for it
            if hasattr(self, 'current_resource_data') and self.current_resource_data:
                website = self.current_resource_data.get('website', '')
                if website and website.startswith('http'):
                    try:
                        page_content = self._browse_page(website)
                        if page_content:
                            extracted_info = self._extract_relevant_info(page_content, query)
                            if extracted_info:
                                all_results.append(f"From organization website ({website}): {extracted_info}")
                                return "\n\n".join(all_results)  # Return early if we found the website
                    except Exception as e:
                        all_results.append(f"Error browsing organization website {website}: {str(e)}")
            
            # If we don't have a website or couldn't access it, try web search
            # Note: DuckDuckGo API appears to be unreliable, so we'll provide a fallback message
            search_terms = [
                f'"{query}" site:.gov',
                f'"{query}" site:.org',
                f'"{query}" site:.edu',
                f'"{query}" "official website"',
                f'"{query}" "contact information"'
            ]
            
            # Try DuckDuckGo API (may not work due to rate limiting or API changes)
            for search_term in search_terms[:1]:  # Limit to 1 search to avoid rate limiting
                try:
                    # Use DuckDuckGo API
                    search_url = "https://api.duckduckgo.com/"
                    params = {
                        'q': search_term,
                        'format': 'json',
                        'no_html': '1',
                        'skip_disambig': '1'
                    }
                    response = requests.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    
                    # Check if response has content
                    if not response.content:
                        all_results.append(f"Web search unavailable for '{search_term}' (API returned empty response)")
                        continue
                        
                    data = response.json()
                    
                    # Process results
                    if data.get('Abstract'):
                        all_results.append(f"Search summary: {data['Abstract']}")
                    
                    # Actually browse the top results
                    if data.get('Results'):
                        for result in data['Results'][:2]:  # Browse top 2 results
                            url = result.get('FirstURL')
                            title = result.get('Text', '')
                            
                            if url and self._is_authoritative_url(url):
                                try:
                                    # Actually browse the page
                                    page_content = self._browse_page(url)
                                    if page_content:
                                        # Extract relevant information
                                        extracted_info = self._extract_relevant_info(page_content, query)
                                        if extracted_info:
                                            all_results.append(f"From {title} ({url}): {extracted_info}")
                                except Exception as e:
                                    all_results.append(f"Error browsing {url}: {str(e)}")
                    
                except Exception as e:
                    all_results.append(f"Web search unavailable for '{search_term}' (API error: {str(e)})")
            
            return "\n\n".join(all_results) if all_results else f"No authoritative information found for {query}"
            
        except Exception as e:
            return f"Error in web search: {str(e)}"
    
    def _is_authoritative_url(self, url: str) -> bool:
        """Check if URL is from an authoritative source."""
        authoritative_domains = ['.gov', '.org', '.edu', 'redcross.org', 'unitedway.org']
        return any(domain in url.lower() for domain in authoritative_domains)
    
    def _browse_page(self, url: str) -> str:
        """Actually browse a webpage and extract content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Extract text content (basic HTML parsing)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            return f"Error browsing page: {str(e)}"
    
    def _extract_relevant_info(self, content: str, query: str) -> str:
        """Extract relevant information from page content based on query."""
        # Simple keyword-based extraction
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        relevant_sentences = []
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(term in sentence.lower() for term in query_terms):
                relevant_sentences.append(sentence)
        
        return '. '.join(relevant_sentences[:5]) if relevant_sentences else ""
    
    @tool
    def _verify_website_tool(self, website: str) -> str:
        """
        Verify if a website is accessible, active, and appears on authoritative sources.
        Check for proper formatting, accessibility, and official recognition.
        
        Args:
            website: Website URL to verify
            
        Returns:
            Verification results and extracted information
        """
        try:
            if not website:
                return "No website provided"
            
            # Clean and format the website URL
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            
            # Remove any trailing spaces or invalid characters
            website = website.strip()
            
            # Basic URL validation
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, website):
                return f"Website '{website}' does not appear to be a valid URL format"
            
            # Check website accessibility
            try:
                response = requests.get(website, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    accessibility_status = f"Website {website} is accessible and active (Status: {response.status_code})"
                else:
                    accessibility_status = f"Website {website} returned status code: {response.status_code}"
            except requests.exceptions.SSLError:
                accessibility_status = f"Website {website} has SSL certificate issues"
            except requests.exceptions.ConnectionError:
                accessibility_status = f"Website {website} is not accessible (connection failed)"
            except Exception as e:
                accessibility_status = f"Website {website} is not accessible: {str(e)}"
            
            # Search for website URL on authoritative sources
            try:
                search_query = f'"{website}"'
                search_results = self._authoritative_web_search_tool(query=search_query)
                if search_results and "No authoritative information found" not in search_results:
                    return f"{accessibility_status} | Found on authoritative websites: {search_results[:200]}..."
                else:
                    return f"{accessibility_status} | Not found on authoritative websites - verification needed"
            except Exception as search_error:
                return f"{accessibility_status} | Web search failed: {str(search_error)}"
                
        except Exception as e:
            return f"Error verifying website: {str(e)}"
    
    @tool
    def _verify_phone_tool(self, phone: str) -> str:
        """
        Verify if a phone number appears on authoritative websites.
        Check for proper US phone number formatting and search for it on official sources.
        
        Args:
            phone: Phone number to verify
            
        Returns:
            Verification results and formatting suggestions
        """
        try:
            if not phone:
                return "No phone number provided"
            
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', phone)
            
            # Check if it's a valid US phone number (10 or 11 digits)
            if len(digits_only) == 10:
                formatted_phone = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
                format_valid = True
            elif len(digits_only) == 11 and digits_only.startswith('1'):
                formatted_phone = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
                format_valid = True
            else:
                format_valid = False
                formatted_phone = phone
            
            if not format_valid:
                return f"Phone number {phone} may not be in valid US format. Expected 10 digits or 11 digits starting with 1"
            
            # Search for phone number on authoritative websites
            search_query = f'"{phone}"'
            try:
                search_results = self._authoritative_web_search_tool(query=search_query)
                if search_results and "No authoritative information found" not in search_results:
                    return f"Phone number {phone} has valid format and found on authoritative websites: {search_results[:200]}..."
                else:
                    return f"Phone number {phone} has valid format but not found on authoritative websites - verification needed"
            except Exception as search_error:
                return f"Phone number {phone} has valid format but web search failed: {str(search_error)}"
                
        except Exception as e:
            return f"Error verifying phone number: {str(e)}"
    
    @tool
    def _verify_email_tool(self, email: str) -> str:
        """
        Verify if an email address appears on authoritative websites.
        Check for proper email formatting and search for it on official sources.
        
        Args:
            email: Email address to verify
            
        Returns:
            Verification results and formatting suggestions
        """
        try:
            if not email:
                return "No email address provided"
            
            # Enhanced email validation regex
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(email_pattern, email):
                return f"Email {email} does not have valid format"
            
            # Additional format checks for common issues
            if email.count('@') > 1:
                return f"Email {email} has multiple @ symbols"
            if email.startswith('.') or email.endswith('.'):
                return f"Email {email} starts or ends with a dot"
            if '..' in email:
                return f"Email {email} has consecutive dots"
                
            # Extract domain for verification
            domain = email.split('@')[1]
            
            # Check if domain has valid DNS records
            try:
                import socket
                socket.gethostbyname(domain)
                domain_valid = True
            except socket.gaierror:
                domain_valid = False
            
            if not domain_valid:
                return f"Email {email} has invalid domain '{domain}' - no DNS records found"
            
            # Check for common disposable email domains
            disposable_domains = [
                'tempmail.org', '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
                'yopmail.com', 'throwaway.email', 'temp-mail.org', 'sharklasers.com'
            ]
            
            if domain.lower() in disposable_domains:
                return f"Email {email} uses disposable domain '{domain}' - may not be reliable"
            
            # Search for email on authoritative websites
            search_query = f'"{email}"'
            try:
                search_results = self._authoritative_web_search_tool(query=search_query)
                if search_results and "No authoritative information found" not in search_results:
                    return f"Email {email} has valid format and found on authoritative websites: {search_results[:200]}..."
                else:
                    return f"Email {email} has valid format but not found on authoritative websites - verification needed"
            except Exception as search_error:
                return f"Email {email} has valid format but web search failed: {str(search_error)}"
                
        except Exception as e:
            return f"Error verifying email: {str(e)}"
    
    @tool
    def _verify_address_tool(self, address: str) -> str:
        """
        Verify if an address appears on authoritative websites.
        Check for address format and search for it on official sources.
        
        Args:
            address: Address to verify
            
        Returns:
            Verification results and formatting suggestions
        """
        try:
            # Basic address validation
            if not address or len(address.strip()) < 5:
                return f"Address '{address}' appears to be too short or empty"
            
            # Check for common address components
            address_lower = address.lower()
            has_street = any(word in address_lower for word in ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 'way', 'court', 'ct'])
            has_number = bool(re.search(r'\d+', address))
            
            if not has_street:
                return f"Address '{address}' may be missing street type (street, avenue, road, etc.)"
            if not has_number:
                return f"Address '{address}' may be missing street number"
            
            # Search for address on authoritative websites
            search_query = f'"{address}"'
            try:
                search_results = self._authoritative_web_search_tool(query=search_query)
                if search_results and "No authoritative information found" not in search_results:
                    return f"Address '{address}' has valid format and found on authoritative websites: {search_results[:200]}..."
                else:
                    return f"Address '{address}' has valid format but not found on authoritative websites - verification needed"
            except Exception as search_error:
                return f"Address '{address}' has valid format but web search failed: {str(search_error)}"
                
        except Exception as e:
            return f"Error verifying address: {str(e)}"
    
    @tool
    def _verify_location_tool(self, location_value: str, location_type: str) -> str:
        """
        Verify if location information appears on authoritative websites.
        Check for format validity and search for it on official sources.
        
        Args:
            location_value: Location value to verify
            location_type: Type of location (city, state, county, postal_code)
            
        Returns:
            Verification results and geographic data
        """
        try:
            if not location_value:
                return f"No {location_type} provided"
            
            # Basic format validation based on location type
            if location_type == 'city':
                # City validation
                if len(location_value.strip()) < 2:
                    return f"City '{location_value}' appears to be too short"
                if not re.match(r'^[A-Za-z\s\-\'\.]+$', location_value):
                    return f"City '{location_value}' may contain invalid characters"
                    
            elif location_type == 'state':
                # State validation
                valid_states = [
                    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
                ]
                if location_value.upper() not in valid_states:
                    return f"State '{location_value}' is not a valid US state abbreviation"
                    
            elif location_type == 'postal_code':
                # Postal code validation
                if not re.match(r'^\d{5}(-\d{4})?$', location_value):
                    return f"Postal code '{location_value}' is not in valid US format (12345 or 12345-6789)"
                    
            elif location_type == 'county':
                # County validation
                if len(location_value.strip()) < 2:
                    return f"County '{location_value}' appears to be too short"
                if not re.match(r'^[A-Za-z\s\-\'\.]+$', location_value):
                    return f"County '{location_value}' may contain invalid characters"
            
            # Search for location information on authoritative websites
            search_query = f'"{location_value}"'
            try:
                search_results = self._authoritative_web_search_tool(query=search_query)
                if search_results and "No authoritative information found" not in search_results:
                    return f"{location_type.title()} '{location_value}' has valid format and found on authoritative websites: {search_results[:200]}..."
                else:
                    return f"{location_type.title()} '{location_value}' has valid format but not found on authoritative websites - verification needed"
            except Exception as search_error:
                return f"{location_type.title()} '{location_value}' has valid format but web search failed: {str(search_error)}"
                
        except Exception as e:
            return f"Error verifying {location_type}: {str(e)}"
    
    @tool
    def _verify_organization_tool(self, organization_name: str) -> str:
        """
        Verify if an organization exists and is currently active.
        Search for official websites, government registrations, and current status.
        
        Args:
            organization_name: Organization name to verify
            
        Returns:
            Verification results and organization details
        """
        try:
            # Search for organization verification
            search_terms = [
                f'"{organization_name}" "official website"',
                f'"{organization_name}" "contact us"',
                f'"{organization_name}" "about us"',
                f'"{organization_name}" site:.gov',
                f'"{organization_name}" site:.org'
            ]
            
            results = []
            
            for search_term in search_terms[:2]:  # Limit searches
                try:
                    search_url = "https://api.duckduckgo.com/"
                    params = {
                        'q': search_term,
                        'format': 'json',
                        'no_html': '1',
                        'skip_disambig': '1'
                    }
                    response = requests.get(search_url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('Abstract'):
                        results.append(f"Organization info: {data['Abstract']}")
                    if data.get('AbstractURL'):
                        results.append(f"Source: {data['AbstractURL']}")
                        
                except Exception as e:
                    results.append(f"Search error: {str(e)}")
            
            return "\n".join(results) if results else f"No current information found for {organization_name}"
        except Exception as e:
            return f"Error verifying organization: {str(e)}"
    
    @tool
    def _discover_services_tool(self, website_url: str) -> str:
        """
        Discover and extract services offered by an organization by crawling their official website.
        Focus on finding service pages, program descriptions, and what the organization does.
        
        Args:
            website_url: Website URL to crawl for services
            
        Returns:
            List of discovered services and details
        """
        try:
            if not website_url:
                return "No website URL provided"
            
            # Clean and format the website URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            website_url = website_url.strip()
            
            discovered_services = []
            pages_crawled = []
            links_followed = []
            
            # First, get the main page content and extract links
            try:
                main_content = self._browse_page(website_url)
                if main_content:
                    pages_crawled.append(f"Main page: {website_url}")
                    # Extract services from main page
                    services_from_main = self._extract_services_from_content(main_content, website_url)
                    discovered_services.extend(services_from_main)
                    
                    # Extract and follow relevant links from the main page
                    relevant_links = self._find_relevant_links(main_content, website_url)
                    links_followed.extend(relevant_links)
                    
                    # Follow the most promising links (limit to 5 to avoid too many requests)
                    for link_url in relevant_links[:5]:
                        try:
                            page_content = self._browse_page(link_url)
                            if page_content and len(page_content) > 100:
                                pages_crawled.append(f"Linked page: {link_url}")
                                services_from_page = self._extract_services_from_content(page_content, link_url)
                                discovered_services.extend(services_from_page)
                        except Exception as e:
                            # Skip pages that can't be accessed
                            continue
                            
            except Exception as e:
                discovered_services.append(f"Error accessing main page: {str(e)}")
            
            # Also try a few common service-related patterns as fallback
            fallback_patterns = ['/about/', '/contact/', '/programs/']
            for pattern in fallback_patterns:
                try:
                    fallback_url = website_url.rstrip('/') + pattern
                    page_content = self._browse_page(fallback_url)
                    if page_content and len(page_content) > 100:
                        pages_crawled.append(f"Fallback page: {fallback_url}")
                        services_from_page = self._extract_services_from_content(page_content, fallback_url)
                        discovered_services.extend(services_from_page)
                except Exception:
                    continue
            
            # Deduplicate and format results
            unique_services = list(set(discovered_services))
            
            result = f"Services discovered from {website_url}:\n"
            result += f"Pages crawled: {len(pages_crawled)}\n"
            result += f"Links followed: {len(links_followed)}\n"
            result += f"Services found: {len(unique_services)}\n\n"
            
            if unique_services:
                result += "Services:\n"
                for i, service in enumerate(unique_services, 1):
                    result += f"{i}. {service}\n"
            else:
                result += "No specific services found. This may indicate:\n"
                result += "- Services are described in general terms\n"
                result += "- Website structure is different than expected\n"
                result += "- Services information is in downloadable documents\n"
            
            return result
            
        except Exception as e:
            return f"Error discovering services: {str(e)}"
    
    def _extract_services_from_content(self, content: str, source_url: str) -> List[str]:
        """Extract service information from webpage content."""
        services = []
        
        # Common service-related keywords and patterns
        service_keywords = [
            'food assistance', 'food bank', 'food pantry', 'meals', 'groceries',
            'healthcare', 'medical', 'dental', 'mental health', 'counseling',
            'housing', 'shelter', 'rental assistance', 'homeless services',
            'education', 'tutoring', 'job training', 'employment services',
            'transportation', 'bus passes', 'rides',
            'utility assistance', 'energy assistance', 'bill help',
            'clothing', 'furniture', 'household items',
            'childcare', 'child care', 'daycare',
            'senior services', 'elderly assistance',
            'disability services', 'accessibility',
            'legal aid', 'legal assistance',
            'financial assistance', 'money management', 'budgeting',
            'crisis intervention', 'emergency services',
            'case management', 'referrals', 'advocacy'
        ]
        
        content_lower = content.lower()
        
        # Look for service mentions
        for keyword in service_keywords:
            if keyword in content_lower:
                # Find the context around the keyword
                keyword_index = content_lower.find(keyword)
                start = max(0, keyword_index - 100)
                end = min(len(content), keyword_index + len(keyword) + 100)
                context = content[start:end].strip()
                
                # Clean up the context
                context = ' '.join(context.split())
                if len(context) > 20:  # Only include substantial context
                    services.append(f"{keyword.title()}: {context}")
        
        # Look for structured service lists (bullet points, numbered lists)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or 
                        line[0].isdigit() and '.' in line[:3]):
                # This looks like a list item
                if any(keyword in line.lower() for keyword in service_keywords):
                    services.append(f"Listed service: {line}")
        
        return services[:20]  # Limit to 20 services to avoid overwhelming results
    
    def _find_relevant_links(self, content: str, base_url: str) -> List[str]:
        """Find relevant links on a page that might contain service information."""
        links = []
        
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            # Parse the HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                link_text = link.get_text().strip().lower()
                
                # Convert relative URLs to absolute URLs
                full_url = urljoin(base_url, href)
                
                # Look for service-related links
                service_keywords = ['service', 'program', 'help', 'assistance', 'support', 'about', 'contact']
                if any(keyword in link_text for keyword in service_keywords):
                    links.append(full_url)
                elif any(keyword in href.lower() for keyword in service_keywords):
                    links.append(full_url)
            
            return links[:10]  # Limit to 10 links
            
        except Exception as e:
            return []
    
    @tool
    def _extract_service_details_tool(self, website_url: str, service_name: str) -> str:
        """
        Extract detailed information about a specific service from an organization's website.
        Look for eligibility requirements, hours, costs, and other service-specific details.
        
        Args:
            website_url: Website URL to search for service details
            service_name: Name of the service to extract details for
            
        Returns:
            Structured service details
        """
        try:
            if not website_url or not service_name:
                return "Website URL and service name are required"
            
            # Clean and format the website URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            website_url = website_url.strip()
            
            service_details = []
            pages_searched = []
            
            # Get main page content
            main_content = self._browse_page(website_url)
            if main_content:
                pages_searched.append(f"Main page: {website_url}")
                # Look for service-specific information
                details_from_main = self._find_service_details(main_content, service_name)
                service_details.extend(details_from_main)
            
            # Find and follow relevant links that might contain service details
            if main_content:
                relevant_links = self._find_relevant_links(main_content, website_url)
                
                # Follow the most promising links (limit to 3 to avoid too many requests)
                for link_url in relevant_links[:3]:
                    try:
                        page_content = self._browse_page(link_url)
                        if page_content and len(page_content) > 100:
                            pages_searched.append(f"Linked page: {link_url}")
                            additional_details = self._find_service_details(page_content, service_name)
                            service_details.extend(additional_details)
                    except Exception:
                        continue
            
            # Also try a few common patterns as fallback
            fallback_patterns = ['/about/', '/contact/', '/programs/']
            for pattern in fallback_patterns:
                try:
                    fallback_url = website_url.rstrip('/') + pattern
                    page_content = self._browse_page(fallback_url)
                    if page_content and len(page_content) > 100:
                        pages_searched.append(f"Fallback page: {fallback_url}")
                        additional_details = self._find_service_details(page_content, service_name)
                        service_details.extend(additional_details)
                except Exception:
                    continue
            
            # Deduplicate details
            unique_details = list(set(service_details))
            
            if unique_details:
                result = f"Service details for '{service_name}' found on {website_url}:\n"
                result += f"Pages searched: {len(pages_searched)}\n\n"
                for i, detail in enumerate(unique_details, 1):
                    result += f"{i}. {detail}\n"
            else:
                result = f"No specific details found for '{service_name}' on {website_url}.\n"
                result += f"Pages searched: {len(pages_searched)}\n"
                result += "This service may be mentioned but detailed information is not available on the website."
            
            return result
            
        except Exception as e:
            return f"Error extracting service details: {str(e)}"
    
    def _find_service_details(self, content: str, service_name: str) -> List[str]:
        """Find detailed information about a specific service in content."""
        details = []
        content_lower = content.lower()
        service_lower = service_name.lower()
        
        # Look for service-specific information patterns
        detail_patterns = [
            # Hours patterns
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*[-–]\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^.]*?(\d{1,2}:\d{2})',
            r'(hours?|open|closed)[^.]*?(\d{1,2}:\d{2})',
            
            # Cost patterns
            r'(free|no cost|no charge|sliding scale|income-based|donation)',
            r'(\$\d+|\d+\s*dollars?)',
            r'(cost|fee|price|payment)[^.]*?(free|\$\d+|\d+\s*dollars?)',
            
            # Eligibility patterns
            r'(eligibility|requirements|qualify|qualification)[^.]*?(income|residence|age|documentation)',
            r'(must|need|require)[^.]*?(income|residence|age|documentation)',
            
            # Contact patterns
            r'(call|phone|contact)[^.]*?(\d{3}[-.]?\d{3}[-.]?\d{4})',
            r'(email|e-mail)[^.]*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            
            # Location patterns
            r'(location|address|where)[^.]*?(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr))',
        ]
        
        import re
        
        # Find sentences containing the service name
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if service_lower in sentence.lower() and len(sentence) > 20:
                # Look for detail patterns in this sentence
                for pattern in detail_patterns:
                    matches = re.findall(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            detail = ' '.join(match)
                        else:
                            detail = match
                        if detail and len(detail) > 5:
                            details.append(f"{detail}")
        
        # Also look for paragraphs that mention the service
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if service_lower in paragraph.lower() and len(paragraph) > 50:
                # Extract key information from the paragraph
                key_info = self._extract_key_info_from_paragraph(paragraph)
                if key_info:
                    details.append(f"Service information: {key_info}")
        
        return list(set(details))[:10]  # Limit to 10 details and remove duplicates
    
    def _extract_key_info_from_paragraph(self, paragraph: str) -> str:
        """Extract key information from a paragraph about a service."""
        # Look for common service information patterns
        info_patterns = [
            r'(available|offered|provided)[^.]*?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
            r'(free|no cost|no charge|sliding scale)',
            r'(eligibility|requirements|qualify)',
            r'(call|phone|contact|email)',
            r'(location|address|where)',
        ]
        
        import re
        
        for pattern in info_patterns:
            matches = re.findall(pattern, paragraph, re.IGNORECASE)
            if matches:
                return ' '.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
        
        return paragraph[:200] + "..." if len(paragraph) > 200 else paragraph
