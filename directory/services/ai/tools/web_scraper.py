"""
AI Web Scraper Module

This module handles web page browsing, content extraction, and link discovery
for the AI Review Service. It provides comprehensive web scraping capabilities
for resource verification and information extraction.

The module includes functionality for:
- Web page browsing with proper headers and timeouts
- Content extraction and text parsing
- Link discovery and following
- Authoritative URL validation
- Relevant information extraction based on queries
- HTML parsing and text cleaning
- Error handling and fallback mechanisms

All scraping operations are designed to be respectful of web servers
with appropriate timeouts, user agents, and error handling.

Dependencies:
    - requests: For HTTP requests and session management
    - beautifulsoup4: For HTML parsing and content extraction
    - urllib.parse: For URL manipulation and validation
    - re: For regular expressions and pattern matching
    - os: For environment variable access
    - dotenv: For environment variable loading

Example:
    >>> scraper = WebScraper()
    >>> content = scraper._browse_page("https://example.org")
    >>> info = scraper._extract_relevant_info(content, "contact information")
    >>> print(info)
"""

import os
import requests
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Constants
REQUEST_TIMEOUT = 15
MAX_CONTENT_LENGTH = 2000

# Load environment variables
load_dotenv()


class WebScraper:
    """
    Web scraping and content extraction functionality for AI verification.
    
    This class handles browsing web pages, extracting relevant information,
    discovering links, and parsing content for service verification. It provides
    comprehensive web scraping capabilities with proper error handling and
    respectful web server interaction.
    
    The scraper uses BeautifulSoup for HTML parsing and requests for HTTP
    operations, with appropriate timeouts and user agents to ensure reliable
    content extraction while being respectful of web servers.
    
    Attributes:
        session: Requests session object with configured headers for web scraping
        
    Methods:
        - _is_authoritative_url: Validate if URL is from authoritative source
        - _browse_page: Browse and extract content from web pages
        - _extract_relevant_info: Extract relevant information based on queries
        - _discover_links: Find and validate links on web pages
        - _follow_links: Follow and extract content from discovered links
        
    Example:
        >>> scraper = WebScraper()
        >>> content = scraper._browse_page("https://example.org")
        >>> if "error" not in content.lower():
        ...     info = scraper._extract_relevant_info(content, "services")
        ...     print(info)
    """
    
    def __init__(self):
        """
        Initialize the web scraper with proper session configuration.
        
        Sets up a requests session with appropriate headers for web scraping,
        including a realistic user agent to avoid being blocked by websites.
        The session is configured to be respectful of web servers while
        providing reliable content extraction capabilities.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _is_authoritative_url(self, url: str) -> bool:
        """
        Check if URL is from an authoritative source.
        
        Validates whether a URL belongs to an authoritative domain that
        is considered reliable for resource verification. Focuses on
        government, educational, and major non-profit organizations.
        
        Args:
            url: URL string to validate for authoritative status
                
        Returns:
            True if the URL is from an authoritative source, False otherwise
            
        Example:
            >>> scraper = WebScraper()
            >>> scraper._is_authoritative_url("https://www.irs.gov")
            True
            >>> scraper._is_authoritative_url("https://example.com")
            False
        """
        authoritative_domains = ['.gov', '.org', '.edu', 'redcross.org', 'unitedway.org']
        return any(domain in url.lower() for domain in authoritative_domains)
    
    def _browse_page(self, url: str) -> str:
        """
        Actually browse a webpage and extract content.
        
        Performs HTTP GET request to the specified URL and extracts
        readable text content from the HTML response. Uses BeautifulSoup
        for HTML parsing and removes script/style elements to focus on
        meaningful content.
        
        The method includes proper error handling, timeouts, and user
        agent headers to ensure reliable content extraction while being
        respectful of web servers.
        
        Args:
            url: URL of the page to browse and extract content from
                
        Returns:
            String containing extracted text content from the webpage.
            Content is limited to 2000 characters to manage response size.
            Returns error message string if browsing fails.
            
        Example:
            >>> scraper = WebScraper()
            >>> content = scraper._browse_page("https://example.org")
            >>> if "error" not in content.lower():
            ...     print(f"Content length: {len(content)}")
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Extract text content (basic HTML parsing)
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
            
            return text[:MAX_CONTENT_LENGTH]  # Limit content length
            
        except Exception as e:
            return f"Error browsing page: {str(e)}"
    
    def _extract_relevant_info(self, content: str, query: str) -> str:
        """
        Extract relevant information from page content based on query.
        
        Analyzes webpage content to find information relevant to the
        specified query. Uses pattern matching and keyword analysis to
        identify contact information, service details, and other relevant
        data that matches the search criteria.
        
        The method looks for common patterns including:
        - Phone numbers and contact information
        - Email addresses
        - Physical addresses
        - Website URLs
        - Service descriptions and details
        
        Args:
            content: Text content extracted from the webpage
            query: Search query to find relevant information (e.g., "contact",
                "services", "hours", "eligibility")
                
        Returns:
            String containing extracted relevant information. Returns empty
            string if no relevant information is found.
            
        Example:
            >>> scraper = WebScraper()
            >>> content = "Contact us at 555-123-4567 or email@example.org"
            >>> info = scraper._extract_relevant_info(content, "contact information")
            >>> print(info)
        """
        try:
            # Simple keyword-based extraction
            content_lower = content.lower()
            query_lower = query.lower()
            
            # Look for contact information patterns
            contact_patterns = [
                r'phone[:\s]*[\d\-\(\)\s]+',
                r'email[:\s]*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'address[:\s]*[^\.]+',
                r'contact[:\s]*[^\.]+',
                r'website[:\s]*https?://[^\s]+'
            ]
            
            relevant_info = []
            
            # Extract contact information
            for pattern in contact_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                if matches:
                    relevant_info.extend(matches[:2])  # Limit to 2 matches per pattern
            
            # Look for sentences containing the query
            sentences = content.split('.')
            for sentence in sentences:
                if query_lower in sentence.lower() and len(sentence) > 20:
                    relevant_info.append(sentence.strip())
                    if len(relevant_info) >= 3:  # Limit to 3 relevant sentences
                        break
            
            return ' | '.join(relevant_info[:5]) if relevant_info else "No specific information found"
            
        except Exception as e:
            return f"Error extracting info: {str(e)}"
    
    def _find_relevant_links(self, content: str, base_url: str) -> List[str]:
        """
        Find relevant links from webpage content that are likely to contain service information.
        
        Args:
            content: HTML content of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of relevant URLs found
        """
        relevant_links = []
        
        # Service-related keywords that indicate relevant pages
        service_keywords = [
            'service', 'program', 'help', 'assistance', 'support',
            'about', 'mission', 'what-we-do', 'our-work',
            'contact', 'location', 'hours', 'eligibility',
            'apply', 'get-help', 'resources', 'clinic',
            'health', 'education', 'housing', 'food',
            'employment', 'job', 'training', 'outreach'
        ]
        
        # Find all links in the content
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, content, re.IGNORECASE)
        
        for link in links:
            # Skip external links, anchors, and non-HTML links
            if (link.startswith('#') or 
                link.startswith('mailto:') or 
                link.startswith('tel:') or
                link.startswith('javascript:') or
                '#' in link):
                continue
            
            # Convert relative links to absolute URLs
            if not link.startswith(('http://', 'https://')):
                link = urljoin(base_url, link)
            
            # Only include links from the same domain
            try:
                parsed_base = urlparse(base_url)
                parsed_link = urlparse(link)
                if parsed_base.netloc != parsed_link.netloc:
                    continue
            except:
                continue
            
            # Score the link based on relevance
            link_lower = link.lower()
            score = 0
            
            # Check if the link contains service-related keywords
            for keyword in service_keywords:
                if keyword in link_lower:
                    score += 1
            
            # Bonus points for specific patterns
            if any(pattern in link_lower for pattern in ['/services/', '/programs/', '/help/', '/about/']):
                score += 2
            
            # Only include links with a minimum relevance score
            if score >= 1:
                relevant_links.append((link, score))
        
        # Sort by relevance score (highest first) and return URLs
        relevant_links.sort(key=lambda x: x[1], reverse=True)
        return [link for link, score in relevant_links]
    
    def _extract_services_from_content(self, content: str, source_url: str) -> List[str]:
        """
        Extract service information from webpage content.
        
        Args:
            content: HTML content to extract services from
            source_url: URL of the source page
            
        Returns:
            List of extracted service information
        """
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
    
    def _find_service_details(self, content: str, service_name: str) -> List[str]:
        """
        Find detailed information about a specific service in content.
        
        Args:
            content: HTML content to search for service details
            service_name: Name of the service to find details for
            
        Returns:
            List of service details found
        """
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
        """
        Extract key information from a paragraph about a service.
        
        Args:
            paragraph: Text paragraph to extract information from
            
        Returns:
            Extracted key information
        """
        # Look for common service information patterns
        info_patterns = [
            r'(available|offered|provided)[^.]*?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
            r'(hours?|open|closed)[^.]*?(\d{1,2}:\d{2})',
            r'(free|no cost|sliding scale|income-based)',
            r'(call|phone|contact)[^.]*?(\d{3}[-.]?\d{3}[-.]?\d{4})',
            r'(eligibility|requirements|qualify)[^.]*?(income|residence|age)',
        ]
        
        for pattern in info_patterns:
            matches = re.findall(pattern, paragraph, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return ' '.join(matches[0])
                else:
                    return matches[0]
        
        return ""
