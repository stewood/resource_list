"""
Verification Tools for AI Review Service

This module provides tools for AI-powered verification of resource data,
specifically focused on service area validation using the CoverageArea database.

The module contains:
- VerificationTools: Main class for managing verification tools
- ValidateServiceAreaTool: Tool for validating geographic service areas

Dependencies:
- django.db.models: For database queries
- langchain_core.tools: For BaseTool class
- directory.models.geographic.coverage_area: For CoverageArea model
"""

import json
from typing import Dict, Any, Optional, List
from django.db.models import Q
from langchain_core.tools import BaseTool
from directory.models.geographic.coverage_area import CoverageArea


class VerificationTools:
    """
    Tools for AI-powered verification of resource data.
    
    This class provides tools that can be used by AI language models
    for comprehensive resource data validation and verification.
    
    The class focuses on service area validation using the CoverageArea
    database to ensure geographic accuracy and scope validation.
    
    Attributes:
        current_resource_data: Current resource data being verified
        
    Example:
        >>> tools = VerificationTools()
        >>> tools.set_resource_data({'name': 'Example Org', 'county': 'Laurel'})
        >>> tool_list = tools._create_tools()
        >>> print(f"Available tools: {len(tool_list)}")
    """
    
    def __init__(self):
        """Initialize the VerificationTools instance."""
        self.current_resource_data = {}
    
    def set_resource_data(self, resource_data: Dict[str, Any]) -> None:
        """
        Set the current resource data for verification.
        
        Args:
            resource_data: Dictionary containing resource data to verify
            
        Example:
            >>> tools = VerificationTools()
            >>> tools.set_resource_data({
            ...     'name': 'Example Organization',
            ...     'website': 'https://example.org',
            ...     'county': 'Laurel'
            ... })
        """
        self.current_resource_data = resource_data
    
    def _create_tools(self) -> List[BaseTool]:
        """
        Create tools for the AI to use.
        
        Returns a list of verification tools that can be used by AI language models
        for resource data validation and verification.
        
        Returns:
            List of BaseTool instances for AI verification including:
                - ValidateServiceAreaTool
                
        Example:
            >>> tools = VerificationTools()
            >>> tool_list = tools._create_tools()
            >>> print(f"Available tools: {len(tool_list)}")
        """
        return [
            ValidateServiceAreaTool()
        ]
    
    def _validate_service_area_tool(self, area_name: str, area_type: str = None) -> str:
        """
        Validate if a service area exists in the database and is within geographic scope.
        
        This tool checks if a service area exists in the CoverageArea database and
        validates that it's within the system's geographic scope. It supports various
        area types including cities, counties, states, and custom areas.
        
        The tool performs fuzzy matching to handle variations in area names and
        provides detailed validation results including whether the area exists,
        its type, and whether it's within the system's geographic scope.
        
        Args:
            area_name: Name of the service area to validate (e.g., "Laurel County, KY", 
                "Kentucky", "United States")
            area_type: Optional type of area to narrow search (CITY, COUNTY, STATE, 
                POLYGON, RADIUS). If not provided, searches all types.
                
        Returns:
            JSON string containing validation results with the following structure:
            {
                "area_name": "Original area name",
                "exists": true/false,
                "valid": true/false,
                "area_type": "Found area type or null",
                "matched_name": "Exact matched name or null",
                "geographic_scope": "in_scope/out_of_scope/unknown",
                "confidence": 0-100,
                "message": "Human-readable validation message"
            }
            
        Example:
            >>> tools = VerificationTools()
            >>> result = tools._validate_service_area_tool("Laurel County, KY", "COUNTY")
            >>> print(result)
        """
        try:
            # Initialize result structure
            result = {
                "area_name": area_name,
                "exists": False,
                "valid": False,
                "area_type": None,
                "matched_name": None,
                "geographic_scope": "unknown",
                "confidence": 0,
                "message": ""
            }
            
            # Clean and normalize the area name
            clean_name = area_name.strip()
            if not clean_name:
                result["message"] = "Empty area name provided"
                return json.dumps(result, indent=2)
            
            # Build query based on area type filter
            query = Q()
            if area_type and area_type.upper() in [choice[0] for choice in CoverageArea.KIND_CHOICES]:
                query &= Q(kind=area_type.upper())
            
            # Try exact match first
            exact_match = CoverageArea.objects.filter(query & Q(name__iexact=clean_name)).first()
            if exact_match:
                result.update({
                    "exists": True,
                    "valid": True,
                    "area_type": exact_match.kind,
                    "matched_name": exact_match.name,
                    "geographic_scope": "in_scope",
                    "confidence": 100,
                    "message": f"Exact match found: {exact_match.name} ({exact_match.kind})"
                })
                return json.dumps(result, indent=2)
            
            # Try partial matches
            partial_matches = CoverageArea.objects.filter(
                query & Q(name__icontains=clean_name)
            ).order_by('name')[:5]
            
            if partial_matches:
                # Find the best match
                best_match = None
                best_score = 0
                
                for match in partial_matches:
                    # Simple similarity scoring
                    match_lower = match.name.lower()
                    clean_lower = clean_name.lower()
                    
                    # Check if all words in clean_name are in match_name
                    clean_words = clean_lower.split()
                    match_words = match_lower.split()
                    
                    word_match_count = sum(1 for word in clean_words if any(word in mw for mw in match_words))
                    score = (word_match_count / len(clean_words)) * 100 if clean_words else 0
                    
                    if score > best_score:
                        best_score = score
                        best_match = match
                
                if best_match and best_score >= 70:  # 70% confidence threshold
                    result.update({
                        "exists": True,
                        "valid": True,
                        "area_type": best_match.kind,
                        "matched_name": best_match.name,
                        "geographic_scope": "in_scope",
                        "confidence": int(best_score),
                        "message": f"Partial match found: {best_match.name} ({best_match.kind}) - {best_score:.0f}% confidence"
                    })
                else:
                    result.update({
                        "exists": False,
                        "valid": False,
                        "geographic_scope": "unknown",
                        "confidence": 0,
                        "message": f"No valid match found for '{clean_name}'. Partial matches were below confidence threshold."
                    })
            else:
                # Check if it's a known out-of-scope area
                out_of_scope_indicators = [
                    "california", "ca", "texas", "tx", "florida", "fl", "new york", "ny",
                    "canada", "mexico", "europe", "asia", "africa", "australia"
                ]
                
                is_out_of_scope = any(indicator in clean_name.lower() for indicator in out_of_scope_indicators)
                
                if is_out_of_scope:
                    result.update({
                        "exists": False,
                        "valid": False,
                        "geographic_scope": "out_of_scope",
                        "confidence": 90,
                        "message": f"Area '{clean_name}' appears to be outside the system's geographic scope"
                    })
                else:
                    result.update({
                        "exists": False,
                        "valid": False,
                        "geographic_scope": "unknown",
                        "confidence": 0,
                        "message": f"Area '{clean_name}' not found in database and geographic scope unclear"
                    })
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "area_name": area_name,
                "exists": False,
                "valid": False,
                "area_type": None,
                "matched_name": None,
                "geographic_scope": "unknown",
                "confidence": 0,
                "message": f"Error validating service area: {str(e)}"
            }
            return json.dumps(error_result, indent=2)


# Tool Class for Service Area Validation
class ValidateServiceAreaTool(BaseTool):
    name: str = "_validate_service_area_tool"
    description: str = """Validate if a service area exists in the database and is within geographic scope.
    
    This tool checks if a service area exists in the CoverageArea database and
    validates that it's within the system's geographic scope. It supports various
    area types including cities, counties, states, and custom areas.
    
    The tool performs fuzzy matching to handle variations in area names and
    provides detailed validation results including whether the area exists,
    its type, and whether it's within the system's geographic scope."""
    
    def _run(self, area_name: str, area_type: str = None) -> str:
        # Create a temporary VerificationTools instance to use the validation method
        tools = VerificationTools()
        return tools._validate_service_area_tool(area_name, area_type)
