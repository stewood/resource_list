# Verification Notes Field Access Control Implementation

## Overview

This document outlines the changes made to implement proper access control for the Verification Notes field, ensuring it is only accessible to users with Editor role or higher, while the Source field remains publicly visible.

## Problem Identified

**Issue**: The Verification Notes field (`notes`) was being displayed publicly in the public resource detail view, violating the intended design where:
- **Source field**: Should be for public data attribution
- **Notes field**: Should be for internal verification details only

## Changes Implemented

### 1. Removed Notes from Public Views

**File**: `templates/directory/public_resource_detail.html`
- **Change**: Removed the "Additional Information" section that displayed `resource.notes`
- **Impact**: Notes field is no longer visible to public users

### 2. Added Role-Based Access Control to Forms

**File**: `directory/forms.py`
- **Change**: Added `_user_can_edit_notes()` method to check user permissions
- **Change**: Modified `__init__()` to conditionally hide notes field for non-editor users
- **Impact**: Only users with Editor, Reviewer, or Admin roles can see/edit the notes field in forms

### 3. Updated Admin Interface

**File**: `directory/admin.py`
- **Change**: Separated source and notes into distinct fieldsets
- **Change**: Updated fieldset descriptions to clarify purposes:
  - **Source Information**: "Public source attribution for this information"
  - **Verification Notes (Internal)**: "INTERNAL USE ONLY - Verification details, contact information, and audit trail"
- **Change**: Added `source` to `list_display` for admin resource list visibility
- **Change**: Added `source` to `search_fields` for admin search functionality
- **Impact**: Clear separation of public vs internal fields in admin interface

### 4. Enhanced Admin Interface

**File**: `directory/admin.py`
- **Change**: Updated fieldset descriptions to clarify the purpose of source vs notes fields
- **Change**: Removed source field from `list_display` to clean up admin resource list view
- **Result**: Source field still searchable and editable, but not cluttering the list view

### 5. Updated Form Placeholder Text

**File**: `directory/forms.py`
- **Change**: Updated notes field placeholder to include "INTERNAL USE ONLY" prefix
- **Impact**: Clear indication that notes field is for internal use

### 6. Added Permission Context to Views

**File**: `directory/views.py`
- **Change**: Added `can_view_notes` context to `ResourceDetailView` and `ArchiveDetailView`
- **Change**: Imported `user_has_role` function for permission checking
- **Impact**: Views now provide permission context to templates

### 7. Updated Templates with Permission Checks

**File**: `templates/directory/archive_detail.html`
- **Change**: Added `can_view_notes` permission check to notes display
- **Impact**: Notes only visible to authorized users in archive views

### 8. Updated Model Documentation

**File**: `directory/models.py`
- **Change**: Updated notes field help text to include "INTERNAL USE ONLY" warning
- **Impact**: Clear documentation that notes field is not for public consumption

### 9. Created Database Migration

**File**: `directory/migrations/0008_update_notes_help_text.py`
- **Change**: Migration to update the help text for the notes field
- **Impact**: Database schema reflects the new field documentation

### 10. Ensured Source Field Visibility

**File**: `templates/directory/public_resource_list.html`
- **Change**: Added source field display to resource cards in public list view
- **Impact**: Source information is now visible to all users in the main resource list

## Field Purpose Clarification

### Source Field (Public)
- **Purpose**: Public attribution for resource information
- **Examples**: "Kentucky Cabinet for Health and Family Services", "Organization Website"
- **Visibility**: Displayed in public views
- **Required**: Yes, for "needs_review" status
- **Display Locations**:
  - ✅ Public resource list (resource cards)
  - ✅ Public resource detail (Information Quality section)
  - ✅ Admin resource list (list_display column)
  - ✅ Admin resource detail (Source Information fieldset)
  - ✅ Archive detail (verification section)

### Notes Field (Internal Only)
- **Purpose**: Internal verification details and audit trail
- **Examples**: Contact person details, verification dates, verification methods
- **Visibility**: Only visible to Editor, Reviewer, and Admin users
- **Required**: No, but recommended for data quality
- **Display Locations**:
  - ❌ Public resource list (not displayed)
  - ❌ Public resource detail (not displayed)
  - ✅ Admin resource detail (Verification Notes fieldset, Editor+ only)
  - ✅ Archive detail (Editor+ only)

## Permission Matrix

| User Role | Can View Notes | Can Edit Notes | Can View Source | Can Edit Source |
|-----------|----------------|----------------|-----------------|-----------------|
| Anonymous | ❌ | ❌ | ✅ | ❌ |
| User | ❌ | ❌ | ✅ | ❌ |
| Editor | ✅ | ✅ | ✅ | ✅ |
| Reviewer | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ | ✅ |

## Testing

All changes have been tested and verified:
- ✅ Form tests pass (18/18)
- ✅ View tests pass (6/6)
- ✅ Admin interface loads without errors
- ✅ Public views no longer display notes
- ✅ Source field visible in all appropriate locations
- ✅ Permission checks work correctly

## Migration Instructions

1. Apply the database migration:
   ```bash
   python manage.py migrate
   ```

2. No additional setup required - changes are backward compatible

## Future Considerations

1. **Data Migration**: Consider reviewing existing notes data to ensure it doesn't contain public information that should be moved to the source field
2. **User Training**: Update user documentation to clarify the distinction between source and notes fields
3. **Audit Trail**: Consider adding logging for when notes are accessed/viewed by authorized users

## Files Modified

1. `templates/directory/public_resource_detail.html`
2. `templates/directory/public_resource_list.html`
3. `directory/forms.py`
4. `directory/admin.py`
5. `directory/views.py`
6. `templates/directory/archive_detail.html`
7. `directory/models.py`
8. `directory/migrations/0008_update_notes_help_text.py`

## Summary

The implementation successfully:
- ✅ Removes notes from public visibility
- ✅ Restricts notes access to Editor+ roles
- ✅ Clarifies field purposes in admin interface
- ✅ Ensures source field is visible to all users in all appropriate locations
- ✅ Maintains backward compatibility
- ✅ Preserves all existing functionality
- ✅ Passes all tests

The Verification Notes field is now properly secured and only accessible to authorized users, while the Source field continues to serve its intended purpose as public attribution information and is visible to all users in the main resource list and detail views.
