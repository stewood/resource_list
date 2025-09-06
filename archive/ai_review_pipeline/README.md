# AI Review Pipeline Archive

This directory contains the archived AI review pipeline that was previously used for automated resource verification. The MCP Server approach has been chosen as the preferred verification method.

## Archived Components

### Services
- `services/ai/` - Complete AI service architecture including:
  - Core review service
  - Verification tools
  - Web scraper
  - Response parser
  - Report generator
  - Utilities

### Views
- `views/ai_api_views.py` - AI API views
- `views/ai_auto_verification_views.py` - Auto verification views
- `views/ai_dashboard_views.py` - AI dashboard views

### Templates
- `templates/ai_dashboard.html` - AI dashboard template
- `templates/ai_dashboard_standalone.html` - Standalone AI dashboard

### Documentation
- `docs/AI_AUTO_VERIFICATION_API.md` - AI auto verification API documentation
- `docs/AI_INTEGRATION.md` - AI integration documentation
- `docs/AI_PIPELINE_TROUBLESHOOTING.md` - AI pipeline troubleshooting guide
- `docs/AI_SERVICE_API_DOCUMENTATION.md` - AI service API documentation
- `docs/ENHANCED_AI_INTEGRATION.md` - Enhanced AI integration documentation
- `docs/sample_ai_response.txt` - Sample AI response

### Scripts
- `scripts/run_ai_verification.py` - AI verification runner script

### Tests
- `test_ai_verification.py` - AI verification tests
- `test_ai_service_integration.py` - AI service integration tests

## Archive Date
January 15, 2025

## Reason for Archive
Replaced with MCP Server approach for resource verification. The MCP Server provides better integration with external tools and more reliable verification capabilities.

## Current Verification Method
MCP Server located at `mcp_server/` directory.
