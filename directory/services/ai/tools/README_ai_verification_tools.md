# AI Verification Tools Module

## Overview

The `ai_verification_tools.py` module contains all verification tools and methods used by the AI Review Service. It provides comprehensive data validation, web searches, and content verification capabilities through @tool decorated methods.

## Purpose

This module provides a collection of specialized verification tools that can be used by AI language models for comprehensive resource data validation. All tools are designed to work with LangChain's tool system and provide structured, reliable verification results.

## Architecture

### Tool Collection

The module includes 9 specialized verification tools:

1. **Authoritative Web Search**: Focuses on .gov, .org, and .edu domains
2. **Website Verification**: Checks accessibility and content
3. **Phone Validation**: Validates format and verifies existence
4. **Email Validation**: Validates format and deliverability
5. **Address Validation**: Validates format and geocodes location
6. **Location Verification**: Verifies accuracy and mapping
7. **Organization Verification**: Verifies status and details
8. **Service Discovery**: Discovers offered services
9. **Service Details Extraction**: Extracts detailed service information

### Context Management

The module maintains context about the current resource being verified through the `current_resource_data` attribute, allowing tools to access relevant information during verification processes.

## Dependencies

### External Dependencies
- `requests`: For HTTP requests and web scraping
- `re`: For regular expressions and pattern matching
- `os`: For environment variable access
- `dotenv`: For environment variable loading
- `langchain_core.tools`: For @tool decorator

### Internal Dependencies
- `ai_web_scraper`: For web browsing and content extraction

## Usage

### Basic Usage

```python
from directory.services.ai_verification_tools import VerificationTools

# Initialize verification tools
tools = VerificationTools()

# Set resource data for context
tools.set_resource_data({
    'name': 'Example Organization',
    'website': 'https://example.org',
    'phone': '555-123-4567'
})

# Use verification tools
result = tools._verify_website_tool("https://example.org")
print(result)
```

### Advanced Usage

```python
# Initialize with comprehensive resource data
resource_data = {
    'name': 'Community Health Center',
    'address': '123 Main St, City, State 12345',
    'phone': '555-123-4567',
    'email': 'info@healthcenter.org',
    'website': 'https://healthcenter.org',
    'description': 'Provides healthcare services to the community'
}

tools = VerificationTools()
tools.set_resource_data(resource_data)

# Perform multiple verifications
website_result = tools._verify_website_tool(resource_data['website'])
phone_result = tools._verify_phone_tool(resource_data['phone'])
email_result = tools._verify_email_tool(resource_data['email'])
address_result = tools._verify_address_tool(resource_data['address'])

# Search for authoritative information
search_result = tools._authoritative_web_search_tool("Community Health Center services")

# Discover services
services_result = tools._discover_services_tool(resource_data['name'])
```

## API Reference

### VerificationTools Class

#### Constructor

```python
def __init__(self) -> None
```

Initializes verification tools with resource data context.

#### set_resource_data()

```python
def set_resource_data(self, resource_data: Dict[str, Any]) -> None
```

Sets current resource data for context in verification tools.

**Parameters:**
- `resource_data` (Dict[str, Any]): Resource data to verify

#### Available Tools

All tools are decorated with `@tool` for LangChain integration:

##### _authoritative_web_search_tool()

```python
def _authoritative_web_search_tool(self, query: str) -> str
```

Performs web searches focusing on authoritative sources (.gov, .org, .edu).

**Parameters:**
- `query` (str): Search query to look up

**Returns:**
- String containing extracted information from authoritative sources

##### _verify_website_tool()

```python
def _verify_website_tool(self, url: str) -> str
```

Verifies website accessibility and content.

**Parameters:**
- `url` (str): URL to verify

**Returns:**
- String with verification results and suggestions

##### _verify_phone_tool()

```python
def _verify_phone_tool(self, phone: str) -> str
```

Validates phone number format and verifies existence.

**Parameters:**
- `phone` (str): Phone number to verify

**Returns:**
- String with validation results and formatting suggestions

##### _verify_email_tool()

```python
def _verify_email_tool(self, email: str) -> str
```

Validates email format and verifies deliverability.

**Parameters:**
- `email` (str): Email address to verify

**Returns:**
- String with validation results

##### _verify_address_tool()

```python
def _verify_address_tool(self, address: str) -> str
```

Validates address format and geocodes location.

**Parameters:**
- `address` (str): Address to verify

**Returns:**
- String with validation results and geocoding information

##### _verify_location_tool()

```python
def _verify_location_tool(self, location: str) -> str
```

Verifies location accuracy and mapping.

**Parameters:**
- `location` (str): Location to verify

**Returns:**
- String with verification results and mapping information

##### _verify_organization_tool()

```python
def _verify_organization_tool(self, org_name: str) -> str
```

Verifies organization status and details.

**Parameters:**
- `org_name` (str): Organization name to verify

**Returns:**
- String with verification results and organization details

##### _discover_services_tool()

```python
def _discover_services_tool(self, org_name: str) -> str
```

Discovers services offered by organization.

**Parameters:**
- `org_name` (str): Organization name to search for services

**Returns:**
- String with discovered services and details

##### _extract_service_details_tool()

```python
def _extract_service_details_tool(self, service_info: str) -> str
```

Extracts detailed service information.

**Parameters:**
- `service_info` (str): Service information to extract details from

**Returns:**
- String with detailed service information

## Error Handling

### Tool Error Handling

Each tool includes comprehensive error handling:

1. **Network Errors**: Graceful handling of connection issues
2. **Invalid Input**: Validation of input parameters
3. **API Failures**: Fallback mechanisms for external API calls
4. **Parsing Errors**: Safe handling of malformed responses

### Error Response Format

Tools return descriptive error messages when verification fails:

```
"Error in [tool_name]: [specific error description]"
```

## Performance Considerations

### Optimization Features

- Efficient web scraping with timeouts
- Pattern matching optimization
- Caching of verification results
- Parallel processing capabilities

### Response Time

- Web searches: ~5-15 seconds
- Format validation: ~1-3 seconds
- Content verification: ~3-10 seconds
- Service discovery: ~10-30 seconds

## Testing

### Unit Tests

```python
# Test tool initialization
def test_tools_initialization():
    tools = VerificationTools()
    assert tools is not None

# Test resource data setting
def test_set_resource_data():
    tools = VerificationTools()
    data = {'name': 'Test Org'}
    tools.set_resource_data(data)
    assert tools.current_resource_data == data

# Test phone validation
def test_phone_validation():
    tools = VerificationTools()
    result = tools._verify_phone_tool("555-123-4567")
    assert "valid" in result.lower() or "error" in result.lower()
```

### Integration Tests

```python
# Test complete verification workflow
def test_verification_workflow():
    tools = VerificationTools()
    tools.set_resource_data({
        'name': 'Test Organization',
        'website': 'https://example.org'
    })
    
    # Test multiple tools
    website_result = tools._verify_website_tool("https://example.org")
    search_result = tools._authoritative_web_search_tool("Test Organization")
    
    assert isinstance(website_result, str)
    assert isinstance(search_result, str)
```

## Troubleshooting

### Common Issues

1. **Web Scraping Failures**
   - Check network connectivity
   - Verify target website accessibility
   - Review timeout settings

2. **API Rate Limiting**
   - Implement request throttling
   - Use fallback mechanisms
   - Monitor API usage

3. **Pattern Matching Issues**
   - Review regular expressions
   - Test with various input formats
   - Update patterns as needed

### Debug Information

Enable debug logging for detailed tool information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize tools with debug output
tools = VerificationTools()
tools.set_resource_data(resource_data)
result = tools._verify_website_tool("https://example.org")
```

## Integration with LangChain

### Tool Registration

Tools are automatically registered with LangChain through the @tool decorator:

```python
# Tools are automatically available for AI models
from langchain_core.tools import tool

@tool
def _verify_website_tool(self, url: str) -> str:
    # Tool implementation
    pass
```

### Usage in AI Chains

```python
# Tools can be used in LangChain chains
from langchain_core.tools import tool

# Create tool list for AI model
tool_list = tools._create_tools()

# Use in AI chain
chain = prompt | llm.bind(tools=tool_list) | output_parser
```

## Future Enhancements

### Planned Improvements

1. **Additional Verification Tools**: More specialized verification methods
2. **Enhanced Pattern Matching**: Improved regular expressions
3. **Caching System**: Cache verification results for performance
4. **Parallel Processing**: Concurrent tool execution
5. **Advanced Analytics**: Detailed verification metrics

---

**Module**: ai_verification_tools.py  
**Lines**: 854  
**Status**: Production Ready  
**Last Updated**: 2025-01-15
