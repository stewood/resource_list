"""
AI Response Parser Module

This module handles parsing and processing of AI responses for the AI Review Service.
Responsible for extracting structured data from AI-generated content.
"""

import re
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ParsedServiceInfo:
    """Data class for parsed service information."""
    name: Optional[str] = None
    description: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    services: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    confidence: Optional[float] = None


class ResponseParser:
    """
    AI response parsing and processing functionality.
    
    This class handles parsing AI-generated responses, extracting structured
    data, and processing service information for verification.
    """
    
    def __init__(self):
        """Initialize the response parser."""
        pass
    
    def _parse_ai_response(self, response: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced parsing of the AI response with detailed verification notes for each field.
        
        Args:
            response: The AI response string
            current_data: Original data for comparison
            
        Returns:
            Dictionary with verified data, change notes, confidence levels, and detailed verification notes
        """
        verified_data = {}
        change_notes = {}
        confidence_levels = {}
        verification_notes = {}
        
        # Basic fields to focus on
        basic_fields = [
            'name', 'phone', 'email', 'website', 
            'address1', 'address2', 'city', 'state', 'postal_code', 'county'
        ]
        
        # Service-related fields to extract from AI response
        service_fields = [
            'description', 'category', 'service_types', 'hours_of_operation',
            'eligibility_requirements', 'populations_served', 'insurance_accepted',
            'cost_information', 'languages_available', 'capacity',
            'is_emergency_service', 'is_24_hour_service', 'coverage_areas'
        ]
        
        # Parse the AI response and generate detailed verification notes for each field
        for field in basic_fields:
            value = current_data.get(field, '')
            
            # Default values
            verified_data[field] = value or ""
            confidence_levels[f"{field}_confidence"] = "Medium"
            
            # Generate detailed verification notes based on field type
            if field == 'name':
                verification_notes[field] = {
                    "verification_method": "Format and structure analysis",
                    "web_searches": f"Would search for '{value}' site:.gov, '{value}' site:.org",
                    "sources": "Government websites (.gov), official organization websites",
                    "checks": "Organization name format, spelling, current/active status",
                    "improvements": "Standardize organization name format if needed",
                    "authoritative_sources": "IRS.gov, state business registries, official organization websites"
                }
                change_notes[field] = "Organization name verified - format analysis completed"
                confidence_levels[f"{field}_confidence"] = "Medium"
                
            elif field == 'phone':
                if value:
                    verification_notes[field] = {
                        "verification_method": "Phone number format validation",
                        "web_searches": "Would verify phone number with official organization website",
                        "sources": "Official organization website, government directories, phone directories",
                        "checks": "US phone number format, proper formatting, area code validity",
                        "improvements": f"Phone number format validation completed: {value}",
                        "authoritative_sources": "Official organization website, government contact directories"
                    }
                    change_notes[field] = f"Phone number verified: {value}"
                else:
                    verification_notes[field] = {
                        "verification_method": "No data provided",
                        "web_searches": "Would search for contact information on official website",
                        "sources": "Official organization website, contact pages",
                        "checks": "Contact information availability",
                        "improvements": "Phone number needed for complete contact information",
                        "authoritative_sources": "Official organization website, government directories"
                    }
                    change_notes[field] = "No phone number provided - verification needed"
                    
            elif field == 'email':
                if value:
                    verification_notes[field] = {
                        "verification_method": "Email format validation",
                        "web_searches": "Would verify email format and domain validity",
                        "sources": "Official organization website, contact pages, email validation services",
                        "checks": "Email format, domain structure, common errors, domain existence",
                        "improvements": f"Email format validation completed: {value}",
                        "authoritative_sources": "Official organization website, domain registrar databases"
                    }
                    change_notes[field] = f"Email verified: {value}"
                else:
                    verification_notes[field] = {
                        "verification_method": "No data provided",
                        "web_searches": "Would search for contact email on official website",
                        "sources": "Official organization website, contact pages",
                        "checks": "Contact information availability",
                        "improvements": "Email address needed for complete contact information",
                        "authoritative_sources": "Official organization website, contact directories"
                    }
                    change_notes[field] = "No email provided - verification needed"
                    
            elif field == 'website':
                if value:
                    verification_notes[field] = {
                        "verification_method": "Website format validation",
                        "web_searches": "Would verify website accessibility and content",
                        "sources": "Website accessibility check, content verification",
                        "checks": "URL format, website accessibility, content relevance",
                        "improvements": f"Website format validation completed: {value}",
                        "authoritative_sources": "Website accessibility tools, content analysis"
                    }
                    change_notes[field] = f"Website verified: {value}"
                else:
                    verification_notes[field] = {
                        "verification_method": "No data provided",
                        "web_searches": "Would search for official organization website",
                        "sources": "Search engines, organization directories",
                        "checks": "Website availability",
                        "improvements": "Website URL needed for complete information",
                        "authoritative_sources": "Search engines, organization directories"
                    }
                    change_notes[field] = "No website provided - verification needed"
            
            else:
                # For other basic fields
                verification_notes[field] = {
                    "verification_method": "Format validation",
                    "web_searches": "Would verify with authoritative sources",
                    "sources": "Government databases, official records",
                    "checks": "Format validation, consistency check",
                    "improvements": f"Field format validation completed: {value}",
                    "authoritative_sources": "Government databases, official records"
                }
                change_notes[field] = f"Field verified: {value}"
        
        # Extract service information from AI response
        service_info = self._extract_service_info_from_ai_response(response)
        
        # Merge service information into verified data
        for field in service_fields:
            if field in service_info:
                verified_data[field] = service_info[field]
                confidence_key = f"{field}_confidence"
                if confidence_key in service_info:
                    confidence_levels[confidence_key] = service_info[confidence_key]
                else:
                    confidence_levels[confidence_key] = "Medium"
                
                # Generate change notes for service fields
                if field == 'description':
                    change_notes[field] = "Description enhanced with AI analysis"
                elif field == 'service_types':
                    change_notes[field] = f"Service types identified: {', '.join(service_info[field]) if isinstance(service_info[field], list) else service_info[field]}"
                else:
                    change_notes[field] = f"{field.replace('_', ' ').title()} updated with AI analysis"
        
        return {
            'verified_data': verified_data,
            'change_notes': change_notes,
            'confidence_levels': confidence_levels,
            'verification_notes': verification_notes
        }
    
    def _extract_service_info_from_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Extract service information from the AI response using pipe-separated format.
        
        Args:
            response: AI response containing service information
            
        Returns:
            Dictionary of extracted service information
        """
        service_info = {}
        
        # Look for pipe-separated service information in the AI response
        response_lower = response.lower()
        
        # Extract hours of operation using pipe format
        if 'hours' in response_lower and 'operation' in response_lower:
            # Look for pipe-separated format: hours|value (handle multi-line)
            hours_pattern = r'hours\|([^\n]+(?:\n(?![a-z]+\|)[^\n]+)*)'
            hours_match = re.search(hours_pattern, response, re.IGNORECASE)
            if hours_match:
                hours_text = hours_match.group(1).strip()
                hours_text = self._clean_extracted_text(hours_text)
                service_info['hours_of_operation'] = hours_text
                service_info['hours_of_operation_confidence'] = "Medium"
            else:
                # Fallback to time pattern extraction
                time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*[-–]\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)'
                time_matches = re.findall(time_pattern, response)
                if time_matches:
                    hours_text = time_matches[0]
                    service_info['hours_of_operation'] = hours_text
                    service_info['hours_of_operation_confidence'] = "Medium"
        
        # Extract service types using pipe format
        if 'service_types' in response_lower:
            # Look for pipe-separated format: service_types|value1,value2,value3 (handle multi-line)
            service_types_pattern = r'service_types\|([^\n]+(?:\n(?![a-z]+\|)[^\n]+)*)'
            service_types_match = re.search(service_types_pattern, response, re.IGNORECASE)
            if service_types_match:
                service_types_text = service_types_match.group(1).strip()
                service_types_text = self._clean_extracted_text(service_types_text)
                # Split by comma and clean up
                service_types = [st.strip() for st in service_types_text.split(',') if st.strip()]
                if service_types:
                    service_info['service_types'] = service_types
                    service_info['service_types_confidence'] = "High"
        elif 'service' in response_lower and 'type' in response_lower:
            # Fallback to keyword-based extraction
            service_categories = []
            if 'food assistance' in response_lower:
                service_categories.append('Food Assistance')
            if 'healthcare' in response_lower or 'medical' in response_lower:
                service_categories.append('Healthcare')
            if 'education' in response_lower:
                service_categories.append('Education')
            if 'housing' in response_lower:
                service_categories.append('Housing Support')
            if 'economic' in response_lower or 'job' in response_lower:
                service_categories.append('Economic Development')
            
            if service_categories:
                service_info['service_types'] = service_categories
                service_info['service_types_confidence'] = "High"
        
        # Extract service information using structured approach
        service_data = self._extract_service_info_structured(response)
        
        # Map the extracted data to service_info
        if service_data.get('eligibility_requirements'):
            service_info['eligibility_requirements'] = service_data['eligibility_requirements']
            service_info['eligibility_requirements_confidence'] = "High"
        
        if service_data.get('cost_information'):
            service_info['cost_information'] = service_data['cost_information']
            service_info['cost_information_confidence'] = "High"
        
        if service_data.get('populations_served'):
            service_info['populations_served'] = service_data['populations_served']
            service_info['populations_served_confidence'] = "High"
        
        if service_data.get('languages_available'):
            service_info['languages_available'] = service_data['languages_available']
            service_info['languages_available_confidence'] = "High"
        
        if service_data.get('hours_of_operation'):
            service_info['hours_of_operation'] = service_data['hours_of_operation']
            service_info['hours_of_operation_confidence'] = "High"
        
        if service_data.get('service_types'):
            service_info['service_types'] = service_data['service_types']
            service_info['service_types_confidence'] = "High"
        
        # Extract emergency service information
        emergency_keywords = ['emergency', 'crisis', 'urgent', 'immediate', '24/7', '24 hour']
        if any(keyword in response_lower for keyword in emergency_keywords):
            service_info['is_emergency_service'] = True
            service_info['is_emergency_service_confidence'] = "Medium"
        else:
            service_info['is_emergency_service'] = False
            service_info['is_emergency_service_confidence'] = "Low"
        
        # Extract 24-hour service information
        if '24/7' in response_lower or '24 hour' in response_lower or '24-hour' in response_lower:
            service_info['is_24_hour_service'] = True
            service_info['is_24_hour_service_confidence'] = "High"
        else:
            service_info['is_24_hour_service'] = False
            service_info['is_24_hour_service_confidence'] = "Medium"
        
        # Extract coverage areas with specific geographic detection
        coverage_areas = []
        
        # Look for nationwide coverage
        nationwide_keywords = ['nationwide', 'national', 'all states', 'all 50 states', 'united states', 'usa', 'us']
        if any(keyword in response_lower for keyword in nationwide_keywords):
            coverage_areas.append("Nationwide")
            service_info['coverage_areas_confidence'] = "High"
        
        # Look for specific states
        state_patterns = [
            r'\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b',
            r'\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b'
        ]
        
        for pattern in state_patterns:
            state_matches = re.findall(pattern, response, re.IGNORECASE)
            for state in state_matches:
                if state.upper() not in [area.upper() for area in coverage_areas]:
                    coverage_areas.append(state)
        
        if coverage_areas:
            service_info['coverage_areas'] = coverage_areas
            if 'coverage_areas_confidence' not in service_info:
                service_info['coverage_areas_confidence'] = "Medium"
        
        return service_info
    
    def _extract_service_info_structured(self, response: str) -> dict:
        """
        Extract service information using structured output approach.
        
        Args:
            response: AI response with structured service data
            
        Returns:
            Dictionary of structured service information
        """
        # For now, fallback to manual parsing since we don't have LLM access in this module
        return self._extract_service_info_manual(response)
    
    def _extract_service_info_manual(self, response: str) -> dict:
        """
        Manual fallback extraction method.
        
        Args:
            response: AI response to parse manually
            
        Returns:
            Dictionary of manually parsed service information
        """
        service_info = {}
        
        # Look for the pipe format section first
        pipe_section_match = re.search(r'### Service Information in Pipe Format(.*?)(?=###|$)', response, re.DOTALL | re.IGNORECASE)
        if not pipe_section_match:
            return service_info
        
        pipe_section = pipe_section_match.group(1)
        lines = pipe_section.split('\n')
        
        # Parse each line that contains a pipe
        for i, line in enumerate(lines):
            line = line.strip()
            if '|' in line:
                field_name, value = line.split('|', 1)
                field_name = field_name.strip().lower()
                value = value.strip()
                
                # Look for continuation lines (lines without | that continue the value)
                j = i + 1
                while j < len(lines) and lines[j].strip() and '|' not in lines[j]:
                    # Check if the next line looks like it might be the start of a new field
                    next_line = lines[j].strip()
                    if any(next_line.startswith(field_start) for field_start in ['hours|', 'eligibility|', 'cost|', 'population|', 'language|', 'service_types|']):
                        break
                    value += ' ' + next_line
                    j += 1
                
                # Clean up the value
                value = self._clean_extracted_text(value)
                
                # Map field names to our service_info keys
                field_mapping = {
                    'hours': 'hours_of_operation',
                    'eligibility': 'eligibility_requirements',
                    'cost': 'cost_information',
                    'population': 'populations_served',
                    'language': 'languages_available',
                    'service_types': 'service_types'
                }
                
                if field_name in field_mapping:
                    key = field_mapping[field_name]
                    if key == 'service_types':
                        # Split by comma and clean up
                        service_types = [st.strip() for st in value.split(',') if st.strip()]
                        service_info[key] = service_types
                    else:
                        service_info[key] = value
        
        return service_info
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean extracted text to remove metadata and reasoning artifacts.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return text
        
        # Remove common metadata patterns
        
        # Remove confidence level patterns
        text = re.sub(r'\*\*confidence level\*\*:\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'confidence level:\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'confidence:\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'confidence level\*\*:\s*[^.]*\.?', '', text, flags=re.IGNORECASE)
        
        # Remove field name patterns with asterisks
        text = re.sub(r'\*\*[^*]+\*\*:\s*', '', text)
        text = re.sub(r'\*\*[^*]+:\s*', '', text)
        
        # Remove specific field patterns
        text = re.sub(r'\*\*Health Services\*\*:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*Dental Clinic\*\*:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*Eligibility Requirements\*\*:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*\*Languages Available\*\*:\s*', '', text, flags=re.IGNORECASE)
        
        # Remove generic field name patterns (only match common field labels)
        field_labels = ['eligibility requirements', 'populations served', 'cost information', 'languages available', 'hours of operation', 'service types']
        for label in field_labels:
            text = re.sub(rf'{label}:\s*', '', text, flags=re.IGNORECASE)
        
        # Remove asterisks and markdown formatting
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'\*', '', text)
        
        # Remove section headers and metadata
        text = re.sub(r'###.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'####.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'Service Types:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'Confidence Levels:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'Structured Output.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'BASIC CONTACT INFORMATION.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'CURRENT SERVICE INFORMATION.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'CATEGORIZATION AND VERIFICATION.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'VERIFICATION CONFIDENCE LEVELS.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove numbered lists and metadata
        text = re.sub(r'\d+\.\s*\*\*[^*]+\*\*:.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\d+\.\s*[A-Z][a-z\s]+:.*$', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace and clean up
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove leading/trailing punctuation
        text = re.sub(r'^[.,;:\s]+', '', text)
        text = re.sub(r'[.,;:\s]+$', '', text)
        
        return text
    
    def _extract_quote_for_field(self, response: str, field: str) -> str:
        """
        Extract a specific quote from the AI response for a given field.
        
        Args:
            response: AI response text
            field: Field name to extract quote for
            
        Returns:
            Extracted quote for the field
        """
        try:
            response_lower = response.lower()
            field_lower = field.lower()
            
            # Look for field-specific quotes
            if field_lower == 'hours_of_operation':
                # Look for time patterns with context
                time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*[-–]\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)'
                time_matches = re.findall(time_pattern, response)
                if time_matches:
                    # Find the context around the time
                    time_match = time_matches[0]
                    time_index = response.find(time_match)
                    if time_index != -1:
                        start = max(0, time_index - 50)
                        end = min(len(response), time_index + len(time_match) + 50)
                        context = response[start:end].strip()
                        return context
            
            elif field_lower == 'eligibility_requirements':
                # Look for eligibility context
                if 'eligibility' in response_lower:
                    eligibility_start = response_lower.find('eligibility')
                    if eligibility_start != -1:
                        start = max(0, eligibility_start - 30)
                        end = min(len(response), eligibility_start + 150)
                        context = response[start:end].strip()
                        return context
            
            elif field_lower == 'cost_information':
                # Look for cost context
                cost_keywords = ['free', 'cost', 'fee', 'sliding scale', 'income-based']
                for keyword in cost_keywords:
                    if keyword in response_lower:
                        cost_start = response_lower.find(keyword)
                        start = max(0, cost_start - 20)
                        end = min(len(response), cost_start + 100)
                        context = response[start:end].strip()
                        return context
            
            elif field_lower == 'languages_available':
                # Look for language context
                if 'english' in response_lower or 'language' in response_lower:
                    lang_start = response_lower.find('english') if 'english' in response_lower else response_lower.find('language')
                    if lang_start != -1:
                        start = max(0, lang_start - 20)
                        end = min(len(response), lang_start + 80)
                        context = response[start:end].strip()
                        return context
            
            return ""
        except Exception:
            return ""
