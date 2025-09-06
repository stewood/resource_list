"""
Pydantic Models for AI Verification Output

This module defines enhanced structured output models for the AI verification system.
These models handle mixed data types (strings, lists, booleans, nulls) to properly
parse comprehensive AI verification results while maintaining backward compatibility.

Author: Resource Directory Team
Created: 2025-08-30
Version: 2.0.0
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class AIVerificationOutput(BaseModel):
    """
    Enhanced structured output for AI verification results.
    
    This model handles mixed data types to properly parse comprehensive AI verification
    output including strings, lists, booleans, and null values.
    """
    
    # Core identification
    resource_name: str = Field(..., description="Name of the resource being verified")
    verification_timestamp: Optional[str] = Field(None, description="Timestamp of verification")
    ai_model_used: Optional[str] = Field(None, description="AI model used for verification")
    
    # Enhanced data fields that can handle mixed types
    verified_data: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Verified field values (can be strings, lists, booleans, or null)"
    )
    confidence_scores: Dict[str, Union[float, None]] = Field(
        default_factory=dict, 
        description="Confidence scores (0-100 or null for missing fields)"
    )
    
    # Additional verification metadata
    verification_statuses: Dict[str, str] = Field(
        default_factory=dict,
        description="Verification status for each field (VERIFIED, UPDATED, CONFLICTING, NOT_FOUND, ERROR, SKIPPED)"
    )
    
    # Sources and reasoning
    sources_used: List[str] = Field(default_factory=list, description="Source URLs used")
    field_sources: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Dictionary of field names to lists of source URLs"
    )
    field_reasoning: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of field names to reasoning explanations"
    )
    change_notes: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of field names to change notes"
    )
    missing_field_recommendations: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of field names to recommendations for finding missing information"
    )
    
    # Summary statistics
    total_fields_processed: int = Field(0, description="Total number of fields processed")
    verified_fields_count: int = Field(0, description="Number of fields successfully verified")
    updated_fields_count: int = Field(0, description="Number of fields updated with new information")
    conflicting_fields_count: int = Field(0, description="Number of fields with conflicting information")
    not_found_fields_count: int = Field(0, description="Number of fields where no information was found")
    average_confidence_score: float = Field(50.0, ge=0, le=100, description="Average confidence score across all fields")
    overall_verification_status: str = Field("not_found", description="Overall verification status")
    
    # General notes
    verification_notes: Optional[str] = Field(None, description="General notes about the verification process")
    
    def get_field_verification(self, field_name: str) -> Dict[str, Any]:
        """Get verification result for a specific field."""
        return {
            "field_name": field_name,
            "verified_value": self.verified_data.get(field_name),
            "confidence_score": self.confidence_scores.get(field_name, 50.0),
            "verification_status": self.verification_statuses.get(field_name, "NOT_FOUND"),
            "sources": self.field_sources.get(field_name, self.sources_used),
            "reasoning": self.field_reasoning.get(field_name, ""),
            "change_notes": self.change_notes.get(field_name, ""),
            "missing_field_recommendations": self.missing_field_recommendations.get(field_name, "")
        }
    
    def get_all_field_verifications(self) -> List[Dict[str, Any]]:
        """Get all field verification results as a list."""
        verifications = []
        all_fields = set(self.verified_data.keys()) | set(self.confidence_scores.keys()) | set(self.verification_statuses.keys())
        
        for field_name in all_fields:
            verifications.append(self.get_field_verification(field_name))
        
        return verifications
    
    def update_backward_compatibility_fields(self):
        """Update backward compatibility fields from structured data."""
        # The verified_data and confidence_scores are already in the right format
        pass
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the verification."""
        return {
            "total_fields_processed": self.total_fields_processed,
            "verified_fields_count": self.verified_fields_count,
            "updated_fields_count": self.updated_fields_count,
            "conflicting_fields_count": self.conflicting_fields_count,
            "not_found_fields_count": self.not_found_fields_count,
            "average_confidence_score": self.average_confidence_score,
            "overall_verification_status": self.overall_verification_status
        }


# Utility functions for working with verification output
def calculate_confidence_score(confidence_level: str) -> float:
    """Convert confidence level to numerical score."""
    confidence_mapping = {
        "VERY_HIGH": 95.0,
        "HIGH": 85.0,
        "MEDIUM": 70.0,
        "LOW": 50.0,
        "VERY_LOW": 25.0,
        "very_high": 95.0,
        "high": 85.0,
        "medium": 70.0,
        "low": 50.0,
        "very_low": 25.0,
    }
    return confidence_mapping.get(confidence_level, 50.0)


def calculate_confidence_level(score: float) -> str:
    """Convert numerical score to confidence level."""
    if score >= 95:
        return "VERY_HIGH"
    elif score >= 85:
        return "HIGH"
    elif score >= 70:
        return "MEDIUM"
    elif score >= 50:
        return "LOW"
    else:
        return "VERY_LOW"


def calculate_confidence_score_from_url(url: str) -> float:
    """Calculate confidence score based on URL source type."""
    if not url or not isinstance(url, str):
        return 50.0
    
    url_lower = url.lower()
    
    # Official websites and government sources (95-100%)
    if any(domain in url_lower for domain in ['.gov', '.edu', '.mil']):
        return 95.0
    
    # Major nonprofit and official organization websites (95-100%)
    if any(domain in url_lower for domain in ['redcross.org', 'unitedway.org', 'salvationarmy.org']):
        return 95.0
    
    # Nonprofit directories and major organizations (85-94%)
    if any(domain in url_lower for domain in ['.org', 'charitynavigator.org', '211.org', 'guidestar.org']):
        return 85.0
    
    # Business directories and verified sources (70-84%)
    if any(domain in url_lower for domain in ['yellowpages.com', 'whitepages.com', 'google.com/maps', 'bing.com/maps']):
        return 70.0
    
    # Social media and user-generated content (50-69%)
    if any(domain in url_lower for domain in ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com']):
        return 50.0
    
    # Unknown or unreliable sources (<50%)
    return 25.0


def parse_ai_verification_response(ai_response: str) -> Optional[AIVerificationOutput]:
    """
    Parse AI verification response and create AIVerificationOutput instance.
    
    This function handles the complex JSON structure from the AI and converts it
    to our enhanced Pydantic model format.
    """
    import json
    import re
    from datetime import datetime
    
    try:
        # Extract JSON from AI response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if not json_match:
            return None
            
        json_str = json_match.group(0)
        parsed_data = json.loads(json_str)
        
        # Extract core fields
        resource_name = parsed_data.get('resource_name', 'Unknown')
        verification_timestamp = parsed_data.get('verification_timestamp', datetime.now().isoformat())
        ai_model_used = parsed_data.get('ai_model_used', 'meta-llama/llama-4-maverick:free')
        
        # Extract verified data from all sections
        verified_data = {}
        confidence_scores = {}
        verification_statuses = {}
        field_sources = {}
        field_reasoning = {}
        change_notes = {}
        missing_field_recommendations = {}
        
        # Process all sections (basic_information, contact_information, address_information, service_information, source_information)
        sections = ['basic_information', 'contact_information', 'address_information', 'service_information', 'source_information']
        
        for section in sections:
            if section in parsed_data:
                for field_name, field_data in parsed_data[section].items():
                    if isinstance(field_data, dict):
                        # Extract verified value (handle different data types)
                        verified_value = field_data.get('verified_value')
                        verified_data[field_name] = verified_value
                        
                        # Extract confidence score
                        confidence_score = field_data.get('confidence_score')
                        if confidence_score is not None:
                            confidence_scores[field_name] = float(confidence_score)
                        
                        # Extract verification status
                        status = field_data.get('status', 'NOT_FOUND')
                        verification_statuses[field_name] = status
                        
                        # Extract sources
                        sources = field_data.get('sources', [])
                        if sources:
                            field_sources[field_name] = sources if isinstance(sources, list) else [sources]
                        
                        # Extract reasoning
                        reasoning = field_data.get('reasoning', '')
                        if reasoning:
                            field_reasoning[field_name] = reasoning
                        
                        # Extract change notes
                        change_note = field_data.get('change_notes', '')
                        if change_note:
                            change_notes[field_name] = change_note
                        
                        # Extract missing field recommendations
                        missing_recommendation = field_data.get('missing_field_recommendations', '')
                        if missing_recommendation:
                            missing_field_recommendations[field_name] = missing_recommendation
        
        # Extract summary information
        summary = parsed_data.get('summary', {})
        total_fields_processed = summary.get('total_fields_processed', len(verified_data))
        verified_fields_count = summary.get('verified_fields_count', 0)
        updated_fields_count = summary.get('updated_fields_count', 0)
        conflicting_fields_count = summary.get('conflicting_fields_count', 0)
        not_found_fields_count = summary.get('not_found_fields_count', 0)
        average_confidence_score = summary.get('average_confidence_score', 50.0)
        overall_verification_status = summary.get('overall_verification_status', 'NOT_FOUND')
        
        # Extract sources used
        sources_used = []
        if 'sources_used' in parsed_data:
            for source in parsed_data['sources_used']:
                if isinstance(source, dict) and 'url' in source:
                    sources_used.append(source['url'])
                elif isinstance(source, str):
                    sources_used.append(source)
        
        # Extract verification notes
        verification_notes = parsed_data.get('verification_notes', '')
        
        # Create AIVerificationOutput instance
        return AIVerificationOutput(
            resource_name=resource_name,
            verification_timestamp=verification_timestamp,
            ai_model_used=ai_model_used,
            verified_data=verified_data,
            confidence_scores=confidence_scores,
            verification_statuses=verification_statuses,
            sources_used=sources_used,
            field_sources=field_sources,
            field_reasoning=field_reasoning,
            change_notes=change_notes,
            missing_field_recommendations=missing_field_recommendations,
            total_fields_processed=total_fields_processed,
            verified_fields_count=verified_fields_count,
            updated_fields_count=updated_fields_count,
            conflicting_fields_count=conflicting_fields_count,
            not_found_fields_count=not_found_fields_count,
            average_confidence_score=average_confidence_score,
            overall_verification_status=overall_verification_status,
            verification_notes=verification_notes
        )
        
    except Exception as e:
        print(f"Error parsing AI verification response: {e}")
        return None
