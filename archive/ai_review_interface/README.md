# AI Review Interface Archive

This directory contains the old manual AI review interface that was replaced by the automated AI verification system.

## Files Archived

- `ai_review_views.py` - The view that handled the manual AI review interface
- `ai_review.html` - The template for the manual AI review page
- `test_ai_review.py` - Tests for the manual AI review functionality

## Why Archived

The manual AI review interface was replaced by an automated system where:
1. AI automatically applies changes to resources
2. Resources are marked as "needs_review" 
3. Users review changes via the "Changes Since Published" view
4. Users can approve/deny the entire change set

## Current System

The AI backend remains active and powers:
- `directory/views/ai_auto_verification_views.py` - Automated AI verification API
- `directory/services/ai/` - AI service backend
- `directory/views/ai_api_views.py` - AI API endpoints

## Restoration

If needed, these files can be restored by:
1. Copying the view back to `directory/views/ai_review_views.py`
2. Copying the template back to `templates/directory/ai_review.html`
3. Adding the URL pattern back to `directory/urls.py`
4. Adding the import back to `directory/views/__init__.py`
5. Adding the "AI Review" button back to `templates/directory/resource_detail.html`
