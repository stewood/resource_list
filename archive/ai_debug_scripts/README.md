# AI Debug Scripts Archive

This directory contains AI-related debugging and testing scripts that were moved from the main codebase due to duplication and redundancy.

## Archived Scripts

### 1. `debug_ai_service.py` (1403 lines)
**Purpose:** Comprehensive CLI debugging tool for AI service
**Functionality:**
- Direct AI service testing (bypasses API layer)
- Detailed logging and analysis of AI verification process
- Applies AI-suggested changes directly to resources
- Generates comprehensive debug reports

**Why archived:** This script duplicates functionality that's better handled through the proper API layer. The direct service approach bypasses Django's architecture and creates maintenance overhead.

### 2. `test_ai_auto_verification.py` (216 lines)
**Purpose:** Test script for AI Auto Verification API
**Functionality:**
- Tests the AI auto verification API endpoint
- Demonstrates proper API usage
- Shows API response handling
- Tests resource verification through HTTP requests

**Why archived:** While this script uses the proper API approach, it's a development/testing script that doesn't belong in the main codebase. The functionality is covered by the actual API endpoints and Django test suite.

### 3. `debug_api_response.py` (106 lines)
**Purpose:** Debug API response logic for GIS bounds
**Functionality:**
- Debugs why bounds are not included in staging API response
- Tests GIS-enabled settings and geometry handling
- Validates coverage area associations
- Tests the exact logic from API views

**Why archived:** This was created to debug a specific GIS-related issue. If the issue is resolved, this script is no longer needed. If the issue persists, it should be addressed in the main codebase rather than through a separate debug script.

## Recommendations

1. **Use the main API endpoints** for AI verification testing
2. **Use Django's test suite** for comprehensive testing
3. **Address GIS issues** in the main codebase if they persist
4. **Keep these scripts for reference** if similar debugging is needed in the future

## Migration Notes

- AI verification functionality is properly implemented in `directory/services/ai/core/review_service.py`
- API endpoints are available at `/api/resources/{id}/ai-auto-verify/`
- Django test suite covers AI functionality in `directory/tests/test_ai_verification.py`

## Archive Date
Archived on: Mon Sep 1 01:12:09 PM CDT 2025
Reason: Code cleanup - removal of duplicate/unused development scripts
