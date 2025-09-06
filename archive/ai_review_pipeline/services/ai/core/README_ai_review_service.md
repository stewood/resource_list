# AI Review Service Module

## Overview

The `ai_review_service.py` module contains the main `AIReviewService` class that orchestrates AI-powered verification and improvement suggestions for resource data. This is the primary interface for the AI verification system.

## Purpose

This module serves as the main orchestrator for the entire AI verification system, using composition to integrate multiple specialized modules while maintaining backward compatibility with existing code.

## Architecture

### Composition Pattern

The main service uses composition to integrate specialized modules:

```
AIReviewService (Main Orchestrator)
├── VerificationTools (Data Validation)
├── WebScraper (Web Content Extraction)
├── ResponseParser (AI Response Processing)
├── ReportGenerator (Report Creation)
└── AIUtilities (Utility Functions)
```

### Key Responsibilities

1. **Service Orchestration**: Coordinates all verification activities
2. **Model Management**: Initializes and manages the AI language model
3. **Tool Integration**: Creates and manages verification tools
4. **Response Processing**: Handles AI responses and generates reports
5. **Error Handling**: Provides robust fallback mechanisms
6. **Public API**: Maintains backward compatibility

## Dependencies

### External Dependencies
- `langchain_openai`: For LLM integration
- `langchain_core`: For prompts and output parsing
- `dotenv`: For environment variable management
- `requests`: For HTTP requests
- `re`: For regular expressions

### Internal Dependencies
- `ai_verification_tools`: Verification tools and methods
- `ai_web_scraper`: Web scraping functionality
- `ai_response_parser`: AI response processing
- `ai_report_generator`: Report generation
- `ai_utilities`: Utility functions

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: API key for OpenRouter (required for AI functionality)

### Model Configuration

- **Model**: meta-llama/llama-4-maverick:free
- **Provider**: OpenRouter
- **Context Window**: 128K tokens
- **Temperature**: 0.1 (low for consistent verification)
- **Max Tokens**: 4000

## Usage

### Basic Usage

```python
from directory.services.ai_review_service import AIReviewService

# Initialize the service
service = AIReviewService()

# Check if service is available
if service.is_available():
    # Verify resource data
    result = service.verify_resource_data({
        'name': 'Example Organization',
        'website': 'https://example.org',
        'phone': '555-123-4567'
    })
    
    # Access results
    print(result['verified_data'])
    print(result['confidence_scores'])
    print(result['report'])
else:
    print("AI service is not available")
```

### Advanced Usage

```python
# Initialize with custom configuration
service = AIReviewService()

# Verify complex resource data
resource_data = {
    'name': 'Community Health Center',
    'address': '123 Main St, City, State 12345',
    'phone': '555-123-4567',
    'email': 'info@healthcenter.org',
    'website': 'https://healthcenter.org',
    'description': 'Provides healthcare services to the community'
}

result = service.verify_resource_data(resource_data)

# Process results
verified_data = result['verified_data']
change_notes = result['change_notes']
confidence_scores = result['confidence_scores']
report = result['report']
ai_response = result['ai_response']

# Check confidence levels
for field, score in confidence_scores.items():
    if score >= 90:
        print(f"{field}: High confidence ({score})")
    elif score >= 70:
        print(f"{field}: Medium confidence ({score})")
    else:
        print(f"{field}: Low confidence ({score})")
```

## API Reference

### AIReviewService Class

#### Constructor

```python
def __init__(self) -> None
```

Initializes the AI review service with all required components.

#### Public Methods

##### verify_resource_data()

```python
def verify_resource_data(self, current_data: Dict[str, Any]) -> Dict[str, Any]
```

Enhanced verification of resource data with comprehensive validation.

**Parameters:**
- `current_data` (Dict[str, Any]): Resource data to verify

**Returns:**
- Dictionary containing verified data, change notes, confidence scores, report, and AI response

##### is_available()

```python
def is_available(self) -> bool
```

Check if the AI service is available and ready for use.

**Returns:**
- True if service is available, False otherwise

## Error Handling

### Fallback Mechanisms

1. **AI Model Unavailable**: Returns fallback response with original data
2. **Module Initialization Failure**: Graceful degradation with error messages
3. **Network Errors**: Continues with available functionality
4. **Parsing Errors**: Uses default values and error reporting

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

## Performance Considerations

### Optimization Features

- Efficient model initialization with testing
- Tool list caching
- Response processing optimization
- Memory management for large responses

### Response Time

- Model initialization: ~2-5 seconds
- Resource verification: ~10-30 seconds (depending on complexity)
- Report generation: ~1-3 seconds

## Testing

### Unit Tests

```python
# Test service initialization
def test_service_initialization():
    service = AIReviewService()
    assert service is not None

# Test availability check
def test_service_availability():
    service = AIReviewService()
    assert isinstance(service.is_available(), bool)

# Test resource verification
def test_resource_verification():
    service = AIReviewService()
    if service.is_available():
        result = service.verify_resource_data({'name': 'Test Org'})
        assert 'verified_data' in result
        assert 'confidence_scores' in result
```

### Integration Tests

```python
# Test complete workflow
def test_complete_workflow():
    service = AIReviewService()
    if service.is_available():
        # Test with real resource data
        resource_data = {
            'name': 'Test Organization',
            'website': 'https://example.org'
        }
        result = service.verify_resource_data(resource_data)
        
        # Verify all expected keys are present
        expected_keys = ['verified_data', 'change_notes', 'confidence_scores', 'report', 'ai_response']
        for key in expected_keys:
            assert key in result
```

## Troubleshooting

### Common Issues

1. **Service Not Available**
   - Check `OPENROUTER_API_KEY` environment variable
   - Verify internet connectivity
   - Check OpenRouter service status

2. **Module Import Errors**
   - Ensure all dependent modules are present
   - Check Python path and import structure
   - Verify module dependencies are installed

3. **Performance Issues**
   - Check network connectivity
   - Monitor memory usage
   - Review timeout settings

### Debug Information

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize service with debug output
service = AIReviewService()
```

## Migration from Monolithic Version

### Backward Compatibility

The refactored service maintains 100% backward compatibility:

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

1. **Maintainability**: Clean separation of concerns
2. **Testability**: Independent module testing
3. **Extensibility**: Easy to add new features
4. **Performance**: Better code organization
5. **Reliability**: Robust error handling

## Future Enhancements

### Planned Improvements

1. **Additional AI Models**: Support for multiple model providers
2. **Caching**: Response caching for improved performance
3. **Parallel Processing**: Concurrent verification tasks
4. **Advanced Analytics**: Detailed performance metrics
5. **Plugin System**: Extensible verification tools

---

**Module**: ai_review_service.py  
**Lines**: 314 (reduced from 3208 - 90.2% reduction)  
**Status**: Production Ready  
**Last Updated**: 2025-01-15
