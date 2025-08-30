# AI Auto Verification API

## Overview

The AI Auto Verification API provides automated AI-powered verification and improvement of resource data. Unlike the manual AI review process, this API automatically applies all AI-suggested changes and marks the resource for review using the existing workflow system.

## Key Features

- **Automated Change Application**: AI suggestions are automatically applied to the resource
- **Existing Workflow Integration**: Uses the existing `needs_review` → `published` workflow
- **Complete Audit Trail**: All AI actions are logged in the audit system
- **No New Interfaces**: Leverages existing review and approval processes

## API Endpoint

### POST `/api/resources/{resource_id}/ai-auto-verify/`

**Description**: Automatically applies AI-suggested changes to a resource and marks it for review.

**Authentication**: Required (LoginRequiredMixin)

**Request**: No body required (just resource ID in URL)

**Response**: JSON with verification results and status update

## Request Example

```bash
curl -X POST \
  http://localhost:8000/api/resources/123/ai-auto-verify/ \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json'
```

## Response Format

### Success Response (200)

```json
{
    "status": "success",
    "message": "AI verification completed and resource marked for review",
    "resource_id": 123,
    "changes_applied": 5,
    "verification_report": "AI verification completed successfully...",
    "confidence_scores": {
        "name": 90.0,
        "phone": 85.0,
        "email": 95.0,
        "website": 88.0,
        "description": 92.0
    },
    "new_status": "needs_review",
    "audit_log_id": 456,
    "verification_timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Responses

#### AI Service Unavailable (503)

```json
{
    "error": "AI service not available. Please check your OpenRouter API key configuration.",
    "status": "unavailable",
    "details": "Make sure OPENROUTER_API_KEY is set in your environment variables"
}
```

#### Resource Not Found (404)

```json
{
    "error": "Resource not found",
    "resource_id": 123,
    "status": "not_found"
}
```

#### Verification Failed (500)

```json
{
    "error": "An error occurred during AI verification: [error details]",
    "status": "error",
    "resource_id": 123
}
```

## Workflow

1. **User calls API** with resource ID
2. **AI service verifies** resource data and generates suggestions
3. **System applies** all AI-suggested changes to the resource
4. **Audit log entry** is created for the AI verification action
5. **Resource status** is updated to `"needs_review"`
6. **User reviews** the resource using existing review interface
7. **User approves/denies** using existing `publish_resource()` or `unpublish_resource()`

## Integration with Existing Workflow

The AI Auto Verification API integrates seamlessly with the existing review workflow:

### Existing Status Flow
```
draft → needs_review → published
     ↑                ↓
     ←── unpublish ───┘
```

### AI Auto Verification Integration
1. **AI applies changes** and sets status to `"needs_review"`
2. **Existing review process** handles approval/denial
3. **Existing audit system** tracks all actions
4. **Existing permission system** controls access

## Fields That Can Be Updated

The AI service can update the following resource fields:

- **Basic Information**: `name`, `description`
- **Contact Information**: `phone`, `email`, `website`
- **Address Information**: `address1`, `address2`, `city`, `state`, `postal_code`, `county`
- **Service Information**: `hours_of_operation`, `eligibility_requirements`, `populations_served`, `cost_information`, `languages_available`

## Audit Trail

All AI auto verification actions are logged in the audit system with:

- **Action Type**: `ai_auto_verification`
- **Changes Applied**: Number of fields updated
- **Confidence Scores**: AI confidence for each field
- **Verification Report**: Detailed AI analysis
- **Timestamp**: When verification occurred

## Usage Examples

### Python Example

```python
import requests

# AI Auto Verification
response = requests.post(
    'http://localhost:8000/api/resources/123/ai-auto-verify/',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

if response.status_code == 200:
    result = response.json()
    print(f"Applied {result['changes_applied']} changes")
    print(f"Resource status: {result['new_status']}")
    print(f"Verification report: {result['verification_report']}")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript Example

```javascript
// AI Auto Verification
fetch('/api/resources/123/ai-auto-verify/', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer YOUR_TOKEN',
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    if (data.status === 'success') {
        console.log(`Applied ${data.changes_applied} changes`);
        console.log(`Resource status: ${data.new_status}`);
        console.log(`Verification report: ${data.verification_report}`);
    } else {
        console.error(`Error: ${data.error}`);
    }
});
```

## Error Handling

### Common Issues

1. **AI Service Unavailable**: Check OpenRouter API key configuration
2. **Resource Not Found**: Verify resource ID exists
3. **Permission Denied**: Ensure user has appropriate permissions
4. **Verification Failed**: Check AI service logs for details

### Troubleshooting

- **OpenRouter API Key**: Set `OPENROUTER_API_KEY` environment variable
- **Database Connection**: Ensure database is running and accessible
- **Permissions**: Verify user has access to the resource
- **Logs**: Check Django logs for detailed error information

## Security Considerations

- **Authentication Required**: All requests must be authenticated
- **Permission Checks**: Uses existing permission system
- **Audit Trail**: All actions are logged for accountability
- **Input Validation**: Resource ID is validated before processing

## Performance Notes

- **AI Processing Time**: Depends on AI service response time
- **Database Updates**: Minimal impact (single resource update)
- **Audit Logging**: Asynchronous logging for performance
- **Caching**: No caching implemented (real-time verification)

## Future Enhancements

- **Bulk Processing**: Support for multiple resources
- **Scheduled Verification**: Automatic verification on schedule
- **Custom Field Mapping**: Configurable field update rules
- **Confidence Thresholds**: Configurable confidence levels for auto-approval
