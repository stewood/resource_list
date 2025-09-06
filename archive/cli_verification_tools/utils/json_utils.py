"""
JSON utility functions for parsing and formatting.

This module contains utilities for extracting JSON from text, parsing website
discovery results, and formatting JSON for display.
"""

import json
from typing import Any, Dict, Optional


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from text that may contain other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON data or error information

    Raises:
        json.JSONDecodeError: If JSON parsing fails
    """
    try:
        # Try to find JSON boundaries
        json_start = text.find('{')
        json_end = text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            return {
                "parse_status": "error",
                "error": "No JSON structure found in text",
                "extracted_data": None
            }

        # Extract the JSON portion
        json_text = text[json_start:json_end]

        # Parse the JSON
        parsed_data = json.loads(json_text)

        return {
            "parse_status": "success",
            "data": parsed_data,
            "json_text": json_text
        }

    except json.JSONDecodeError as e:
        return {
            "parse_status": "error",
            "error": f"Failed to parse JSON: {str(e)}",
            "raw_text": text
        }
    except Exception as e:
        return {
            "parse_status": "error",
            "error": f"Failed to extract JSON: {str(e)}",
            "raw_text": text
        }


def parse_website_discovery_result(raw_result: str) -> Dict[str, Any]:
    """
    Parse the website discovery result from Cursor Agent to extract structured data.

    Args:
        raw_result: Raw text response from Cursor Agent

    Returns:
        Dictionary with parsed website discovery data
    """
    try:
        # Try to extract JSON from the response
        json_start = raw_result.find('{')
        json_end = raw_result.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            return {
                "parse_status": "error",
                "error": "No JSON structure found in website discovery response",
                "extracted_data": None
            }

        # Extract the JSON portion
        json_text = raw_result[json_start:json_end]

        try:
            # Parse the JSON
            parsed_json = json.loads(json_text)

            # Validate and structure the parsed data
            structured_data = {
                "parse_status": "success",
                "search_strategy": parsed_json.get("search_strategy", ""),
                "urls": parsed_json.get("urls_found", []),  # The JSON has "urls_found" as the array
                "total_urls": parsed_json.get("total_urls", 0),
                "search_notes": parsed_json.get("search_notes", "")
            }

            # Add URL statistics by type
            urls_by_type = {}
            for url_data in structured_data["urls"]:
                url_type = url_data.get("type", "other")
                if url_type not in urls_by_type:
                    urls_by_type[url_type] = []
                urls_by_type[url_type].append(url_data)

            structured_data["urls_by_type"] = urls_by_type
            structured_data["url_type_counts"] = {url_type: len(urls) for url_type, urls in urls_by_type.items()}

            return structured_data

        except json.JSONDecodeError as json_error:
            return {
                "parse_status": "error",
                "error": f"Failed to parse JSON: {str(json_error)}",
                "raw_text": json_text,
                "extracted_data": None
            }

    except Exception as e:
        return {
            "parse_status": "error",
            "error": f"Failed to parse website discovery result: {str(e)}",
            "raw_text": raw_result,
            "extracted_data": None
        }


def format_json_for_display(data: Any) -> str:
    """
    Format JSON data for display with proper indentation and formatting.

    Args:
        data: Data to format as JSON

    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    except Exception as e:
        return f"Error formatting JSON: {str(e)}"


def parse_field_verification_result(raw_result: str) -> Dict[str, Any]:
    """
    Parse the field verification result from Cursor Agent to extract structured data.

    Args:
        raw_result: Raw text response from Cursor Agent

    Returns:
        Dictionary with parsed field verification data
    """
    try:
        # Try to extract JSON from the response
        json_start = raw_result.find('{')
        json_end = raw_result.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            return {
                "parse_status": "error",
                "error": "No JSON structure found in field verification response",
                "extracted_data": None
            }

        # Extract the JSON portion
        json_text = raw_result[json_start:json_end]

        try:
            # Parse the JSON
            parsed_json = json.loads(json_text)

            # Validate and structure the parsed data
            structured_data = {
                "parse_status": "success",
                "resource_name": parsed_json.get("resource_name", ""),
                "category": parsed_json.get("category", ""),
                "description": parsed_json.get("description", ""),
                "address": parsed_json.get("address", ""),
                "city_region_served": parsed_json.get("city_region_served", ""),
                "accessibility_notes": parsed_json.get("accessibility_notes", ""),
                "phone": parsed_json.get("phone", ""),
                "email": parsed_json.get("email", ""),
                "website": parsed_json.get("website", ""),
                "social_media": parsed_json.get("social_media", ""),
                "sources": parsed_json.get("sources", []),
                "verification_notes": parsed_json.get("verification_notes", "")
            }

            # Create field results for tracking what was verified
            field_results = []
            field_mapping = {
                "resource_name": "Resource Name",
                "category": "Category",
                "description": "Description",
                "address": "Address",
                "city_region_served": "Location",
                "phone": "Phone",
                "email": "Email",
                "website": "Website",
                "social_media": "Social Media"
            }

            for field_key, field_name in field_mapping.items():
                if structured_data.get(field_key):
                    field_results.append({
                        "field": field_key,
                        "field_name": field_name,
                        "status": "verified",
                        "confidence": 0.9,
                        "value": structured_data[field_key]
                    })

            structured_data["field_results"] = field_results
            structured_data["fields_verified"] = len(field_results)

            return structured_data

        except json.JSONDecodeError as json_error:
            return {
                "parse_status": "error",
                "error": f"Failed to parse JSON: {str(json_error)}",
                "raw_text": json_text,
                "extracted_data": None
            }

    except Exception as e:
        return {
            "parse_status": "error",
            "error": f"Failed to parse field verification result: {str(e)}",
            "raw_text": raw_result,
            "extracted_data": None
        }


def validate_website_discovery_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate website discovery JSON structure and content.

    Args:
        data: Parsed website discovery data

    Returns:
        Validation result with any issues found
    """
    issues = []

    # Check required fields
    required_fields = ["search_strategy", "urls_found", "total_urls"]
    for field in required_fields:
        if field not in data:
            issues.append(f"Missing required field: {field}")

    # Check URLs structure
    if "urls_found" in data:
        urls = data["urls_found"]
        if not isinstance(urls, list):
            issues.append("urls_found should be a list")
        else:
            for i, url_data in enumerate(urls):
                if not isinstance(url_data, dict):
                    issues.append(f"URL at index {i} should be a dictionary")
                    continue

                required_url_fields = ["url", "type", "description", "confidence"]
                for field in required_url_fields:
                    if field not in url_data:
                        issues.append(f"URL at index {i} missing required field: {field}")

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }

