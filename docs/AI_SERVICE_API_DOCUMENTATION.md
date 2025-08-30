# AI Service API Documentation

## Overview

The AI Review Service has been refactored from a monolithic 3208-line file into a modular architecture with 6 specialized modules. This document provides comprehensive API documentation for the new modular structure.

## Architecture

### Modular Design

The service uses a **composition pattern** where the main `AIReviewService` class orchestrates multiple specialized modules:

```
AIReviewService (Main Orchestrator)
├── VerificationTools (Data Validation)
├── WebScraper (Web Content Extraction)
├── ResponseParser (AI Response Processing)
├── ReportGenerator (Report Creation)
└── AIUtilities (Utility Functions)
```

### Design Principles

1. **Backward Compatibility**: All existing public API methods remain unchanged
2. **Single Responsibility**: Each module has one clear, focused purpose
3. **Composition over Inheritance**: Main service composes other modules
4. **Database Integration**: Service types and categories from database with fallbacks
5. **Robust Error Handling**: Graceful fallbacks when dependencies unavailable

## Main Service API

### AIReviewService Class

**Location**: `directory/services/ai_review_service.py`

**Purpose**: Main orchestrator for AI-powered resource data verification

#### Constructor

```python
def __init__(self) -> None
```

**Description**: Initializes the AI review service with all required components.

**Initialization Process**:
1. Sets up language model (meta-llama/llama-4-maverick:free from OpenRouter)
2. Initializes all specialized modules through composition
3. Creates tool list for AI verification

**Dependencies**:
- `OPENROUTER_API_KEY` environment variable
- All specialized modules (VerificationTools, WebScraper, etc.)

#### Public Methods

##### verify_resource_data()

```python
def verify_resource_data(self, current_data: Dict[str, Any]) -> Dict[str, Any]
```

**Purpose**: Enhanced verification of resource data with comprehensive validation.

**Parameters**:
- `current_data` (Dict[str, Any]): Resource data to verify
  - Expected keys: name, address, phone, email, website, etc.

**Returns**:
- `Dict[str, Any]` containing:
  - `verified_data`: Dict with verified and improved resource data
  - `change_notes`: Dict with notes about changes made
  - `confidence_scores`: Dict with confidence scores (0-100) for each field
  - `report`: String with comprehensive verification report
  - `ai_response`: String with raw AI response for debugging

**Verification Process**:
1. Basic information validation (name, address, phone, email, website)
2. Service discovery and categorization
3. Detailed service information extraction (hours, eligibility, costs)
4. Confidence scoring for all verifications
5. Comprehensive report generation

**Example**:
```python
service = AIReviewService()
result = service.verify_resource_data({
    'name': 'Example Organization',
    'website': 'https://example.org',
    'phone': '555-123-4567'
})
print(result['verified_data']['name'])
print(result['confidence_scores']['name'])
```

##### is_available()

```python
def is_available(self) -> bool
```

**Purpose**: Check if the AI service is available and ready for use.

**Returns**:
- `True` if AI service is available and ready
- `False` if model failed to initialize or is unavailable

**Example**:
```python
service = AIReviewService()
if service.is_available():
    result = service.verify_resource_data(data)
else:
    print("AI service is not available")
```

## Module APIs

### 1. VerificationTools Module

**Location**: `directory/services/ai_verification_tools.py`

**Purpose**: Collection of verification tools for AI-powered resource data validation

#### Class: VerificationTools

##### Constructor

```python
def __init__(self) -> None
```

**Description**: Initializes verification tools with resource data context.

##### set_resource_data()

```python
def set_resource_data(self, resource_data: Dict[str, Any]) -> None
```

**Purpose**: Set current resource data for context in verification tools.

**Parameters**:
- `resource_data` (Dict[str, Any]): Resource data to verify

##### Available Tools

All tools are decorated with `@tool` for LangChain integration:

1. **`_authoritative_web_search_tool(query: str) -> str`**
   - Performs web searches focusing on authoritative sources (.gov, .org, .edu)
   - Browses pages and extracts relevant information

2. **`_verify_website_tool(url: str) -> str`**
   - Verifies website accessibility and content
   - Checks for proper URL format and accessibility

3. **`_verify_phone_tool(phone: str) -> str`**
   - Validates phone number format and verifies existence
   - Suggests proper formatting

4. **`_verify_email_tool(email: str) -> str`**
   - Validates email format and verifies deliverability

5. **`_verify_address_tool(address: str) -> str`**
   - Validates address format and geocodes location

6. **`_verify_location_tool(location: str) -> str`**
   - Verifies location accuracy and mapping

7. **`_verify_organization_tool(org_name: str) -> str`**
   - Verifies organization status and details

8. **`_discover_services_tool(org_name: str) -> str`**
   - Discovers services offered by organization

9. **`_extract_service_details_tool(service_info: str) -> str`**
   - Extracts detailed service information

### 2. WebScraper Module

**Location**: `directory/services/ai_web_scraper.py`

**Purpose**: Web scraping and content extraction functionality

#### Class: WebScraper

##### Constructor

```python
def __init__(self) -> None
```

**Description**: Initializes web scraper with proper session configuration.

##### _is_authoritative_url()

```python
def _is_authoritative_url(self, url: str) -> bool
```

**Purpose**: Check if URL is from an authoritative source.

**Parameters**:
- `url` (str): URL to validate

**Returns**:
- `True` if authoritative (.gov, .org, .edu, etc.), `False` otherwise

##### _browse_page()

```python
def _browse_page(self, url: str) -> str
```

**Purpose**: Browse webpage and extract content.

**Parameters**:
- `url` (str): URL to browse

**Returns**:
- Extracted text content (limited to 2000 characters)
- Error message if browsing fails

##### _extract_relevant_info()

```python
def _extract_relevant_info(self, content: str, query: str) -> str
```

**Purpose**: Extract relevant information from page content based on query.

**Parameters**:
- `content` (str): Text content from webpage
- `query` (str): Search query to find relevant information

**Returns**:
- Extracted relevant information or empty string

### 3. ResponseParser Module

**Location**: `directory/services/ai_response_parser.py`

**Purpose**: AI response parsing and processing

#### Class: ResponseParser

##### _parse_ai_response()

```python
def _parse_ai_response(self, response: str, current_data: Dict[str, Any]) -> Dict[str, Any]
```

**Purpose**: Parse AI response and extract structured data.

**Parameters**:
- `response` (str): Raw AI response
- `current_data` (Dict[str, Any]): Original resource data

**Returns**:
- Dictionary with parsed results including verified_data, change_notes, confidence_levels

### 4. ReportGenerator Module

**Location**: `directory/services/ai_report_generator.py`

**Purpose**: Verification report generation

#### Class: ReportGenerator

##### _generate_verification_report()

```python
def _generate_verification_report(self, current_data: Dict[str, Any], verified_data: Dict[str, Any], 
                                change_notes: Dict[str, str], confidence_levels: Dict[str, str],
                                verification_notes: Dict[str, str], ai_response: str) -> str
```

**Purpose**: Generate comprehensive verification report.

**Parameters**:
- `current_data`: Original resource data
- `verified_data`: Verified and improved data
- `change_notes`: Notes about changes made
- `confidence_levels`: Confidence levels for each field
- `verification_notes`: Additional verification notes
- `ai_response`: Raw AI response

**Returns**:
- Formatted markdown string with complete verification report

### 5. AIUtilities Module

**Location**: `directory/services/ai_utilities.py`

**Purpose**: Utility functions and database integration

#### Class: AIUtilities

**Features**:
- Database integration for service types and categories
- Fallback to hardcoded lists when Django unavailable
- Utility functions for data formatting and cleaning
- Theme extraction and enhanced description creation

## Database Integration

### Service Types and Categories

The utilities module fetches service types and categories from the database:

```python
# Database query for service types
service_types = ServiceType.objects.values_list('name', flat=True)

# Database query for categories  
categories = Category.objects.values_list('name', flat=True)
```

### Fallback Strategy

When Django is not available (e.g., during testing), the system falls back to hardcoded lists:

```python
# Fallback service types
FALLBACK_SERVICE_TYPES = [
    'Healthcare', 'Education', 'Food Assistance', 'Housing',
    'Transportation', 'Employment', 'Legal Services', 'Mental Health'
]

# Fallback categories
FALLBACK_CATEGORIES = [
    'Emergency Services', 'Health & Wellness', 'Education & Training',
    'Food & Nutrition', 'Housing & Shelter', 'Transportation',
    'Employment & Training', 'Legal & Advocacy'
]
```

## Error Handling

### Fallback Mechanisms

1. **AI Model Unavailable**: Returns fallback response with original data
2. **Database Unavailable**: Uses hardcoded service types and categories
3. **Web Scraping Fails**: Continues with available information
4. **Network Errors**: Graceful degradation with error messages

### Error Response Format

```python
{
    'verified_data': original_data.copy(),
    'change_notes': {'status': 'Error description'},
    'confidence_scores': {'overall': 50.0},
    'report': 'User-friendly error message',
    'ai_response': 'Debug error message'
}
```

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: API key for OpenRouter (required for AI functionality)

### Model Configuration

- **Model**: meta-llama/llama-4-maverick:free
- **Provider**: OpenRouter
- **Context Window**: 128K tokens
- **Temperature**: 0.1 (low for consistent verification)
- **Max Tokens**: 4000

## Performance Considerations

### Response Time Optimization

- Content extraction limited to 2000 characters
- Web scraping timeout of 15 seconds
- Single search term limit to avoid rate limiting
- Efficient HTML parsing with BeautifulSoup

### Memory Management

- Session reuse for HTTP requests
- Content length limits
- Proper cleanup of parsed content

## Migration Guide

### From Monolithic to Modular

The refactoring maintains 100% backward compatibility:

```python
# Old usage (still works)
from directory.services.ai_review_service import AIReviewService
service = AIReviewService()
result = service.verify_resource_data(data)

# New usage (same interface)
from directory.services.ai_review_service import AIReviewService
service = AIReviewService()
result = service.verify_resource_data(data)
```

### Benefits of New Architecture

1. **Maintainability**: Each module has focused responsibility
2. **Testability**: Modules can be tested independently
3. **Extensibility**: Easy to add new verification tools
4. **Performance**: Better code organization and efficiency
5. **Reliability**: Robust fallback mechanisms

## Troubleshooting

### Common Issues

1. **AI Model Not Available**
   - Check `OPENROUTER_API_KEY` environment variable
   - Verify internet connectivity
   - Check OpenRouter service status

2. **Database Integration Issues**
   - System automatically falls back to hardcoded lists
   - Check Django database configuration
   - Verify database connectivity

3. **Web Scraping Failures**
   - Check network connectivity
   - Verify target website accessibility
   - Review timeout settings

### Debug Information

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Improvements

1. **Additional Verification Tools**: More specialized verification methods
2. **Enhanced Web Scraping**: Better content extraction algorithms
3. **Performance Optimization**: Caching and parallel processing
4. **Extended Database Integration**: More comprehensive data sources
5. **Advanced Reporting**: Enhanced report formats and analytics

---

**Last Updated**: 2025-01-15  
**Version**: 2.0 (Modular Architecture)  
**Compatibility**: 100% backward compatible with previous version
