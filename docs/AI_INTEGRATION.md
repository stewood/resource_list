# AI Integration Documentation

## Overview

This document describes the AI integration for the Resource Directory application, which uses LangChain to provide AI-powered data verification and improvement suggestions.

## Features

- **AI-Powered Data Verification**: Automatically verify and suggest improvements for resource data
- **Change Notes Generation**: AI generates explanatory notes for suggested changes
- **Fallback Support**: Graceful handling when AI service is unavailable
- **Real-time Integration**: Seamless integration with the existing AI Review interface

## Architecture

### Components

1. **AIReviewService** (`directory/services/ai_review_service.py`)
   - Core service for AI-powered data verification
   - Uses LangChain with OpenAI's GPT models
   - Handles data formatting and response parsing

2. **AIVerificationView** (`directory/views/ai_api_views.py`)
   - REST API endpoint for AI verification requests
   - Handles authentication and error responses
   - Returns structured JSON responses

3. **Frontend Integration** (`templates/directory/ai_review.html`)
   - JavaScript integration with the AI API
   - Real-time updates to the AI Review interface
   - Error handling and user feedback

### Data Flow

1. User clicks "Run AI Verification" button
2. Frontend makes POST request to `/manage/api/resources/{id}/ai-verify/`
3. Backend retrieves resource data and sends to AI service
4. AI service processes data and returns verification results
5. Backend formats response and returns to frontend
6. Frontend updates the interface with verified data and change notes

## Setup

### Prerequisites

1. **OpenRouter API Key**: You need a valid OpenRouter API key
2. **Environment Variables**: Set `OPENROUTER_API_KEY` in your environment

### Installation

1. Install dependencies:
   ```bash
   pip install langchain langchain-openai langchain-community python-dotenv
   ```

2. Set up environment variables:
   ```bash
   export OPENROUTER_API_KEY="your-openrouter-api-key-here"
   ```

3. Test the integration:
   ```bash
   python test_ai_integration.py
   ```

## Configuration

### AI Model Settings

The AI service is configured with the following settings:

- **Provider**: OpenRouter (access to multiple AI models)
- **Primary Model**: `anthropic/claude-3.5-haiku-20241022` (best free model for tool use)
- **Fallback Models**: 
  - `mistralai/mixtral-8x7b-instruct` (good free alternative)
  - `meta-llama/llama-3.1-8b-instruct` (budget-friendly option)
- **Temperature**: `0.1` (low for consistent results)
- **Max Tokens**: Default (varies by model)
- **Tool Use**: Enabled for web search and verification

### Customization

You can customize the AI behavior by modifying:

1. **Prompt Template**: Edit the prompt in `AIReviewService.verify_resource_data()`
2. **Model Selection**: Change the model in `AIReviewService._initialize_llm()`
3. **Response Parsing**: Modify `AIReviewService._parse_ai_response()`

## API Endpoints

### POST `/manage/api/resources/{id}/ai-verify/`

**Purpose**: Trigger AI verification for a specific resource

**Authentication**: Required (LoginRequiredMixin)

**Request**: No body required

**Response**:
```json
{
  "status": "success",
  "verified_data": {
    "name": "Verified Resource Name",
    "phone": "555-123-4567",
    // ... other fields
  },
  "change_notes": {
    "name": "Standardized resource name format",
    "phone": "Phone number format verified",
    // ... other notes
  },
  "resource_id": 123
}
```

**Error Responses**:
- `404`: Resource not found
- `503`: AI service unavailable
- `500`: Internal server error

## Usage

### Basic Usage

1. Navigate to a resource's AI Review page
2. Click the "Run AI Verification" button
3. Wait for AI processing to complete
4. Review the suggested changes and notes
5. Apply changes if desired

### Error Handling

The system handles various error scenarios:

- **No API Key**: Shows fallback message
- **API Errors**: Displays user-friendly error messages
- **Network Issues**: Retry functionality
- **Invalid Data**: Graceful degradation

## Testing

### Manual Testing

1. Start the development server
2. Navigate to `/manage/resources/{id}/ai-review/`
3. Click "Run AI Verification"
4. Verify the results appear correctly

### Automated Testing

Run the test script:
```bash
python test_ai_integration.py
```

## Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Authentication**: All AI endpoints require authentication
3. **Rate Limiting**: Consider implementing rate limiting for production
4. **Data Privacy**: Ensure sensitive data is handled appropriately

## Future Enhancements

1. **Structured Output**: Implement structured output parsing for more reliable results
2. **Batch Processing**: Support for verifying multiple resources at once
3. **Custom Prompts**: Allow users to customize verification prompts
4. **Model Selection**: Support for different AI models
5. **Caching**: Cache AI responses to reduce API calls
6. **Analytics**: Track AI verification usage and success rates

## Troubleshooting

### Common Issues

1. **"AI service not available"**
   - Check that `OPENROUTER_API_KEY` is set
   - Verify the API key is valid
   - Check network connectivity

2. **"AI verification failed"**
   - Check server logs for detailed error messages
   - Verify the resource exists
   - Check API rate limits

3. **Slow response times**
   - Consider using a faster model
   - Implement caching
   - Check network latency

### Debug Mode

Enable debug logging by setting:
```python
import logging
logging.getLogger('directory.services.ai_review_service').setLevel(logging.DEBUG)
```

## Support

For issues related to AI integration:

1. Check the troubleshooting section above
2. Review server logs for error details
3. Test with the provided test script
4. Verify OpenRouter API key and quota status
