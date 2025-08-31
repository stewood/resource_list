#!/usr/bin/env python3
"""
Comprehensive CLI Debugging Tool for AI Service

This tool provides detailed debugging information for the AI review service,
showing all prompts, inputs, outputs, tool calls, and results in real-time.

Usage:
    python debug_ai_service.py --resource-id 123
    python debug_ai_service.py --resource-id 123 --update
    python debug_ai_service.py --test-data
    python debug_ai_service.py --test-tools
    python debug_ai_service.py --verbose --resource-id 123
"""

import os
import sys
import json
import argparse
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_directory.settings')
import django
django.setup()

from directory.models import Resource
from directory.services.ai.core.review_service import AIReviewService

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_debug.log')
    ]
)

logger = logging.getLogger(__name__)


class AIServiceDebugger:
    """Comprehensive debugger for AI service with detailed logging and analysis."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.debug_log = []
        self.start_time = datetime.now()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
    
    def log_step(self, step: str, data: Any = None, level: str = "INFO"):
        """Log a debugging step with optional data."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "data": data,
            "level": level
        }
        self.debug_log.append(log_entry)
        
        if level == "DEBUG" and not self.verbose:
            return
        
        print(f"\n[{timestamp}] {level}: {step}")
        if data:
            if isinstance(data, dict):
                print(json.dumps(data, indent=2, default=str))
            else:
                print(str(data))
    
    def debug_resource_verification_with_update(self, resource_id: int) -> Dict[str, Any]:
        """Debug AI verification for a specific resource AND update it like the API process."""
        print(f"\n{'='*80}")
        print(f"🔍 AI SERVICE DEBUG WITH UPDATE - RESOURCE ID: {resource_id}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Load resource
            self.log_step("Loading resource from database", {"resource_id": resource_id})
            resource = Resource.objects.get(pk=resource_id)
            self.log_step("Resource loaded successfully", {
                "name": resource.name,
                "id": resource.id,
                "category": resource.category.name if resource.category else None,
                "current_status": resource.status
            })
            
            # Step 2: Initialize AI service
            self.log_step("Initializing AI service")
            ai_service = AIReviewService()
            
            if not ai_service.is_available():
                self.log_step("AI service not available", level="ERROR")
                return {"error": "AI service not available"}
            
            self.log_step("AI service initialized successfully")
            
            # Step 3: Prepare resource data (same as API process)
            self.log_step("Preparing resource data for verification")
            current_data = self._prepare_resource_data(resource)
            self.log_step("Resource data prepared", {"fields_count": len(current_data)})
            
            # Step 4: Run AI verification
            self.log_step("Starting AI verification process")
            start_time = time.time()
            
            result = ai_service.verify_resource_data(current_data)
            
            execution_time = time.time() - start_time
            self.log_step("AI verification completed", {
                "execution_time_seconds": execution_time,
                "has_verified_data": bool(result.get('verified_data')),
                "has_change_notes": bool(result.get('change_notes'))
            })
            
            if not result or not result.get('verified_data'):
                self.log_step("AI verification failed or returned no results", level="ERROR")
                return {"error": "AI verification failed"}
            
            # Step 5: Apply changes to resource (same as API process)
            self.log_step("Applying AI changes to resource")
            changes_applied = self._apply_ai_changes(resource, result['verified_data'])
            
            # Step 6: Store AI verification report
            self.log_step("Storing AI verification report")
            self._store_ai_verification_report(resource, result, current_data)
            
            # Step 7: Create audit log entry
            self.log_step("Creating audit log entry")
            audit_log = self._create_ai_verification_audit(resource, result, changes_applied)
            
            # Step 8: Mark resource as needs_review
            self.log_step("Marking resource as needs_review")
            resource.status = "needs_review"
            resource.save()
            
            # Step 9: Generate summary
            summary = self._generate_update_summary(result, changes_applied, audit_log)
            
            self.log_step("Resource update completed successfully", summary)
            
            return {
                "success": True,
                "resource_id": resource_id,
                "changes_applied": changes_applied,
                "new_status": "needs_review",
                "audit_log_id": audit_log.id if audit_log else None,
                "execution_time": execution_time,
                "summary": summary,
                "verification_result": result
            }
            
        except Resource.DoesNotExist:
            self.log_step(f"Resource {resource_id} not found", level="ERROR")
            return {"error": f"Resource {resource_id} not found"}
        except Exception as e:
            self.log_step(f"Error in resource verification with update: {str(e)}", level="ERROR")
            return {"error": str(e)}
    
    def _prepare_resource_data(self, resource: Resource) -> Dict[str, Any]:
        """Prepare resource data for AI verification (same as API process)."""
        # Get current service areas through the ResourceCoverage through model
        from directory.models import ResourceCoverage
        
        current_service_areas = []
        if hasattr(resource, 'coverage_areas'):
            resource_coverage_associations = ResourceCoverage.objects.filter(
                resource=resource
            ).select_related('coverage_area', 'created_by')
            
            current_service_areas = [
                {
                    "area_name": association.coverage_area.name,
                    "area_type": association.coverage_area.kind,
                    "validation_status": "VALID",  # Assume existing areas are valid
                    "confidence_score": 100.0,
                    "geographic_scope": "in_scope",
                    "source": "existing_database",
                    "validation_message": f"Existing service area: {association.coverage_area.name} ({association.coverage_area.kind})",
                    "attached_at": association.created_at.isoformat() if association.created_at else None,
                    "attached_by": association.created_by.username if association.created_by else None
                }
                for association in resource_coverage_associations
            ]
        
        return {
            # Basic information
            "name": resource.name,
            "description": resource.description,
            "category": resource.category.name if resource.category else None,
            
            # Contact information
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            
            # Address information
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            
            # Service information
            "hours_of_operation": resource.hours_of_operation,
            "eligibility_requirements": resource.eligibility_requirements,
            "populations_served": resource.populations_served,
            "cost_information": resource.cost_information,
            "languages_available": resource.languages_available,
            
            # Additional context
            "source": resource.source,
            "notes": resource.notes,
            "service_types": [st.name for st in resource.service_types.all()] if resource.service_types.exists() else [],
            
            # Service areas information
            "current_service_areas": current_service_areas,
        }
    
    def _apply_ai_changes(self, resource: Resource, verified_data: Dict[str, Any]) -> int:
        """Apply AI-suggested changes to the resource (same as API process)."""
        changes_applied = 0
        
        # Define field mappings (AI field names to Resource field names)
        field_mappings = {
            'name': 'name',
            'description': 'description',
            'phone': 'phone',
            'email': 'email',
            'website': 'website',
            'address1': 'address1',
            'address2': 'address2',
            'city': 'city',
            'state': 'state',
            'postal_code': 'postal_code',
            'county': 'county',
            'hours_of_operation': 'hours_of_operation',
            'eligibility_requirements': 'eligibility_requirements',
            'populations_served': 'populations_served',
            'cost_information': 'cost_information',
            'languages_available': 'languages_available',
        }
        
        # Apply changes for each field
        for ai_field, resource_field in field_mappings.items():
            if ai_field in verified_data and verified_data[ai_field]:
                current_value = getattr(resource, resource_field, None)
                new_value = verified_data[ai_field]
                
                # Check if the value has actually changed
                if current_value != new_value:
                    setattr(resource, resource_field, new_value)
                    changes_applied += 1
                    self.log_step(f"Applied AI change to {resource_field}: {current_value} -> {new_value}", level="DEBUG")
        
        # Handle service types (many-to-many field)
        if 'service_types' in verified_data and verified_data['service_types']:
            try:
                from directory.models import ServiceType
                
                # Get the suggested service type names
                suggested_service_types = verified_data['service_types']
                if isinstance(suggested_service_types, str):
                    # Split by comma if it's a string
                    suggested_service_types = [st.strip() for st in suggested_service_types.split(',') if st.strip()]
                
                # Get current service types
                current_service_types = set(resource.service_types.values_list('name', flat=True))
                
                # Find or create service types
                new_service_types = []
                for service_type_name in suggested_service_types:
                    service_type, created = ServiceType.objects.get_or_create(
                        name=service_type_name,
                        defaults={'description': f'Service type for {service_type_name}'}
                    )
                    new_service_types.append(service_type)
                
                # Check if there are any changes
                new_service_type_names = {st.name for st in new_service_types}
                if current_service_types != new_service_type_names:
                    # Clear existing service types and add new ones
                    resource.service_types.clear()
                    resource.service_types.add(*new_service_types)
                    changes_applied += 1
                    self.log_step(f"Applied service types changes: {current_service_types} -> {new_service_type_names}")
                else:
                    self.log_step("Service types unchanged, no update needed", level="DEBUG")
                    
            except Exception as e:
                self.log_step(f"Failed to apply service types changes: {str(e)}", level="ERROR")
                # Continue with other changes even if service types fail
        
        # Handle service areas (many-to-many field through ResourceCoverage)
        if 'service_areas' in verified_data and verified_data['service_areas']:
            try:
                service_area_changes = self._update_resource_service_areas(
                    resource=resource,
                    service_areas_data=verified_data['service_areas']
                )
                changes_applied += service_area_changes
                self.log_step(f"Applied {service_area_changes} service area changes to resource {resource.id}")
            except Exception as e:
                self.log_step(f"Failed to apply service area changes: {str(e)}", level="ERROR")
                # Continue with other changes even if service areas fail
        
        # Save the resource if any changes were made
        if changes_applied > 0:
            resource.save()
            self.log_step(f"Saved {changes_applied} changes to resource")
        else:
            self.log_step("No changes to apply")
        
        return changes_applied
    
    def _update_resource_service_areas(self, resource: Resource, service_areas_data: Dict[str, Any]) -> int:
        """
        Update resource service areas based on AI discoveries and recommendations.
        
        This method processes the service_areas data from AI verification and
        applies changes to the resource's coverage areas through the ResourceCoverage
        through model, maintaining a complete audit trail.
        
        Args:
            resource: The Resource instance to update
            service_areas_data: Dictionary containing service area data from AI
            
        Returns:
            Number of service area changes applied
        """
        from directory.models import CoverageArea, ResourceCoverage
        
        changes_applied = 0
        
        try:
            # Get current service areas
            current_associations = ResourceCoverage.objects.filter(resource=resource)
            current_area_names = set(assoc.coverage_area.name for assoc in current_associations)
            
            # Process discovered areas (new areas to add)
            discovered_areas = service_areas_data.get('discovered_areas', [])
            areas_to_add = []
            
            for area_data in discovered_areas:
                if isinstance(area_data, dict):
                    area_name = area_data.get('area_name')
                    area_type = area_data.get('area_type', 'COUNTY')
                    validation_status = area_data.get('validation_status', 'UNKNOWN')
                    geographic_scope = area_data.get('geographic_scope', 'unknown')
                    
                    # Only add areas that are valid and in scope
                    if (validation_status == 'VALID' and 
                        geographic_scope == 'in_scope' and 
                        area_name and 
                        area_name not in current_area_names):
                        
                        # Find or create the coverage area
                        coverage_area, created = CoverageArea.objects.get_or_create(
                            name=area_name,
                            kind=area_type,
                            defaults={
                                'ext_ids': {},
                                'created_by': None,  # No user for debug script
                                'updated_by': None
                            }
                        )
                        
                        # Create the association if it doesn't exist
                        association, created = ResourceCoverage.objects.get_or_create(
                            resource=resource,
                            coverage_area=coverage_area,
                            defaults={
                                'created_by': None,  # No user for debug script
                                'notes': f'Added via AI auto-verification. Confidence: {area_data.get("confidence_score", "unknown")}'
                            }
                        )
                        
                        if created:
                            areas_to_add.append(area_name)
                            changes_applied += 1
                            self.log_step(f"Added service area '{area_name}' to resource {resource.id}")
            
            # Process recommendations (add/remove based on AI suggestions)
            recommendations = service_areas_data.get('recommendations', [])
            
            for rec in recommendations:
                if isinstance(rec, dict):
                    action = rec.get('action', '').lower()
                    area_name = rec.get('area_name')
                    reason = rec.get('reason', 'AI recommendation')
                    
                    if action == 'add' and area_name and area_name not in current_area_names:
                        # Find or create the coverage area
                        coverage_area, created = CoverageArea.objects.get_or_create(
                            name=area_name,
                            kind=rec.get('area_type', 'COUNTY'),
                            defaults={
                                'ext_ids': {},
                                'created_by': None,  # No user for debug script
                                'updated_by': None
                            }
                        )
                        
                        # Create the association
                        association, created = ResourceCoverage.objects.get_or_create(
                            resource=resource,
                            coverage_area=coverage_area,
                            defaults={
                                'created_by': None,  # No user for debug script
                                'notes': f'Added via AI recommendation: {reason}'
                            }
                        )
                        
                        if created:
                            areas_to_add.append(area_name)
                            changes_applied += 1
                            self.log_step(f"Added recommended service area '{area_name}' to resource {resource.id}")
                    
                    elif action == 'remove' and area_name and area_name in current_area_names:
                        # Remove the association
                        removed_count = ResourceCoverage.objects.filter(
                            resource=resource,
                            coverage_area__name=area_name
                        ).delete()[0]
                        
                        if removed_count > 0:
                            changes_applied += 1
                            self.log_step(f"Removed service area '{area_name}' from resource {resource.id}")
            
            # Log summary of changes
            if areas_to_add:
                self.log_step(f"Added {len(areas_to_add)} new service areas to resource {resource.id}: {', '.join(areas_to_add)}")
            
            return changes_applied
            
        except Exception as e:
            self.log_step(f"Error updating service areas for resource {resource.id}: {str(e)}", level="ERROR")
            return 0
    
    def _store_ai_verification_report(self, resource: Resource, ai_result: Dict[str, Any], original_data: Dict[str, Any]) -> None:
        """Store AI verification report in resource notes."""
        try:
            # Get the concise verification report
            report = ai_result.get('report', 'No report available')
            
            # Replace existing notes with the new report (don't append)
            resource.notes = report
            
            # Set verification fields for published resources
            from django.utils import timezone
            resource.last_verified_at = timezone.now()
            resource.last_verified_by = None  # No user for automated process
            
            resource.save()
            self.log_step("AI verification report stored in resource notes")
            
        except Exception as e:
            self.log_step(f"Failed to store AI verification report: {str(e)}", level="ERROR")
    
    def _create_ai_verification_audit(self, resource: Resource, ai_result: Dict[str, Any], changes_applied: int):
        """Create audit log entry for AI verification."""
        try:
            from audit.models import AuditManager
            
            audit_manager = AuditManager()
            
            # Create audit entry
            audit_entry = audit_manager.log_action(
                actor=None,  # No user for automated process
                action="ai_verification",
                target_table="directory_resource",
                target_id=str(resource.id),
                metadata={
                    "ai_verification": True,
                    "changes_applied": changes_applied,
                    "confidence_scores": ai_result.get('confidence_scores', {}),
                    "verification_report": ai_result.get('report', ''),
                    "ai_response": ai_result.get('ai_response', ''),
                    "notes": f"AI verification completed. Applied {changes_applied} changes."
                }
            )
            
            self.log_step(f"Created audit log entry: {audit_entry.id}")
            return audit_entry
            
        except Exception as e:
            self.log_step(f"Failed to create audit log: {str(e)}", level="ERROR")
            return None
    
    def _generate_update_summary(self, result: Dict[str, Any], changes_applied: int, audit_log) -> Dict[str, Any]:
        """Generate summary of the update process."""
        return {
            "total_fields_verified": len(result.get('verified_data', {})),
            "fields_with_changes": changes_applied,
            "audit_log_created": audit_log is not None,
            "new_status": "needs_review",
            "confidence_scores": result.get('confidence_scores', {}),
            "issues_found": 0  # Could be enhanced to detect issues
        }

    def debug_resource_verification(self, resource_id: int) -> Dict[str, Any]:
        """Debug AI verification for a specific resource."""
        print(f"\n{'='*80}")
        print(f"🔍 AI SERVICE DEBUG - RESOURCE ID: {resource_id}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Load resource
            self.log_step("Loading resource from database", {"resource_id": resource_id})
            resource = Resource.objects.get(pk=resource_id)
            self.log_step("Resource loaded successfully", {
                "name": resource.name,
                "id": resource.id,
                "category": resource.category.name if resource.category else None
            })
            
            # Step 2: Initialize AI service
            self.log_step("Initializing AI service")
            ai_service = AIReviewService()
            
            if not ai_service.is_available():
                self.log_step("AI service not available", level="ERROR")
                return {"error": "AI service not available"}
            
            self.log_step("AI service initialized", {
                "model": getattr(ai_service.llm, 'model_name', 'Unknown'),
                "available": ai_service.is_available()
            })
            
            # Step 3: Prepare data
            self.log_step("Preparing resource data for AI verification")
            current_data = self._prepare_resource_data(resource)
            self.log_step("Resource data prepared", {
                "fields_count": len(current_data),
                "fields": list(current_data.keys())
            })
            
            if self.verbose:
                self.log_step("Full resource data", current_data, level="DEBUG")
            
            # Step 4: Run AI verification with detailed logging
            self.log_step("Starting AI verification process")
            result = self._debug_ai_verification(ai_service, current_data)
            
            # Step 5: Analyze results
            self.log_step("Analyzing verification results")
            analysis = self._analyze_results(result, current_data)
            
            # Step 6: Generate summary
            self.log_step("Generating debug summary")
            summary = self._generate_summary(result, analysis)
            
            return {
                "success": True,
                "resource_id": resource_id,
                "resource_name": resource.name,
                "verification_result": result,
                "analysis": analysis,
                "summary": summary,
                "debug_log": self.debug_log,
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Resource.DoesNotExist:
            self.log_step(f"Resource {resource_id} not found", level="ERROR")
            return {"error": f"Resource {resource_id} not found"}
        except Exception as e:
            self.log_step(f"Error during debugging: {str(e)}", level="ERROR")
            return {"error": str(e)}
    
    def _prepare_resource_data(self, resource: Resource) -> Dict[str, Any]:
        """Prepare resource data for AI verification."""
        return {
            "name": resource.name,
            "description": resource.description,
            "phone": resource.phone,
            "email": resource.email,
            "website": resource.website,
            "address1": resource.address1,
            "address2": resource.address2,
            "city": resource.city,
            "state": resource.state,
            "postal_code": resource.postal_code,
            "county": resource.county,
            "category": resource.category.name if resource.category else None,
            "service_types": [st.name for st in resource.service_types.all()],
            "source": resource.source,
            "notes": resource.notes,
        }
    
    def _debug_ai_verification(self, ai_service: AIReviewService, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI verification with detailed debugging and performance tracking."""
        self.log_step("Calling AI service verify_resource_data method")
        
        # Performance tracking
        start_time = datetime.now()
        
        try:
            # Capture the AI response
            result = ai_service.verify_resource_data(current_data)
            
            # Performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.log_step("AI verification completed", {
                "has_verified_data": "verified_data" in result,
                "has_change_notes": "change_notes" in result,
                "has_confidence_levels": "confidence_levels" in result,
                "has_verification_notes": "verification_notes" in result,
                "execution_time_seconds": execution_time
            })
            
            # Enhanced logging for structured output
            if "verified_data" in result:
                self.log_step("Structured output analysis", {
                    "total_fields": len(result["verified_data"]),
                    "field_names": list(result["verified_data"].keys())
                })
            
            # Log confidence scores if available
            if "confidence_scores" in result:
                confidence_scores = result["confidence_scores"]
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
                self.log_step("Confidence analysis", {
                    "average_confidence": round(avg_confidence, 2),
                    "confidence_range": f"{min(confidence_scores.values()) if confidence_scores else 0} - {max(confidence_scores.values()) if confidence_scores else 0}",
                    "high_confidence_fields": len([s for s in confidence_scores.values() if s >= 85])
                })
            
            # Log verification statuses if available
            if "verification_statuses" in result:
                statuses = result["verification_statuses"]
                status_counts = {}
                for status in statuses.values():
                    status_counts[status] = status_counts.get(status, 0) + 1
                self.log_step("Verification status distribution", status_counts)
            
            # Log missing field recommendations if available
            if "missing_field_recommendations" in result:
                missing_recs = result["missing_field_recommendations"]
                self.log_step("Missing field recommendations", {
                    "total_missing_fields": len(missing_recs),
                    "fields_with_recommendations": list(missing_recs.keys())
                })
                for field, recommendation in missing_recs.items():
                    self.log_step(f"Missing field recommendation for {field}", {
                        "field": field,
                        "recommendation": recommendation
                    }, level="DEBUG")
            
            if self.verbose:
                self.log_step("Full AI response", result, level="DEBUG")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.log_step(f"Error in AI verification after {execution_time:.2f}s: {str(e)}", level="ERROR")
            raise
    
    def _analyze_results(self, result: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the verification results."""
        analysis = {
            "fields_verified": 0,
            "fields_with_changes": 0,
            "confidence_distribution": {},
            "verification_methods": {},
            "issues_found": [],
            "improvements_suggested": []
        }
        
        verified_data = result.get("verified_data", {})
        change_notes = result.get("change_notes", {})
        confidence_levels = result.get("confidence_levels", {})
        verification_notes = result.get("verification_notes", {})
        
        # Analyze each field
        for field_name in verified_data.keys():
            analysis["fields_verified"] += 1
            
            original_value = original_data.get(field_name, "")
            verified_value = verified_data.get(field_name, "")
            change_note = change_notes.get(field_name, "")
            confidence = confidence_levels.get(f"{field_name}_confidence", "Unknown")
            verification_note = verification_notes.get(field_name, {})
            
            # Track confidence distribution
            if confidence not in analysis["confidence_distribution"]:
                analysis["confidence_distribution"][confidence] = 0
            analysis["confidence_distribution"][confidence] += 1
            
            # Track verification methods
            if verification_note and isinstance(verification_note, dict):
                method = verification_note.get("verification_method", "Unknown")
                if method not in analysis["verification_methods"]:
                    analysis["verification_methods"][method] = 0
                analysis["verification_methods"][method] += 1
            
            # Check for changes
            if original_value != verified_value:
                analysis["fields_with_changes"] += 1
                analysis["improvements_suggested"].append({
                    "field": field_name,
                    "original": original_value,
                    "verified": verified_value,
                    "note": change_note
                })
            
            # Check for issues
            if "error" in str(change_note).lower() or "failed" in str(change_note).lower():
                analysis["issues_found"].append({
                    "field": field_name,
                    "issue": change_note
                })
        
        return analysis
    
    def _generate_summary(self, result: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the debugging session."""
        return {
            "total_fields_verified": analysis["fields_verified"],
            "fields_with_changes": analysis["fields_with_changes"],
            "confidence_distribution": analysis["confidence_distribution"],
            "verification_methods_used": analysis["verification_methods"],
            "issues_found": len(analysis["issues_found"]),
            "improvements_suggested": len(analysis["improvements_suggested"]),
            "ai_response_length": len(result.get("ai_response", "")),
            "has_web_search_results": "web search" in str(result).lower(),
            "has_authoritative_sources": "authoritative" in str(result).lower()
        }
    
    def test_individual_tools(self) -> Dict[str, Any]:
        """Test individual AI tools with detailed debugging and performance tracking."""
        print(f"\n{'='*80}")
        print("🔧 TESTING INDIVIDUAL AI TOOLS")
        print(f"{'='*80}")
        
        ai_service = AIReviewService()
        
        if not ai_service.is_available():
            self.log_step("AI service not available for tool testing", level="ERROR")
            return {"error": "AI service not available"}
        
        test_results = {}
        performance_metrics = {}
        
        # Test current tools (DuckDuckGo search + PullMdLoader)
        self.log_step("Testing current 2-tool system")
        
        # Test DuckDuckGo search tool
        self.log_step("Testing DuckDuckGo search tool")
        try:
            start_time = datetime.now()
            # Test with a simple search
            search_tool = ai_service._create_tools()[0]  # First tool should be web_search
            search_result = search_tool.run("Red Cross services")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_results["web_search"] = {
                "success": True, 
                "result": search_result[:500] + "..." if len(search_result) > 500 else search_result,
                "execution_time": execution_time
            }
            performance_metrics["web_search"] = {
                "execution_time": execution_time,
                "result_length": len(search_result)
            }
            self.log_step("DuckDuckGo search successful", {
                "result_length": len(search_result),
                "execution_time": execution_time
            })
        except Exception as e:
            test_results["web_search"] = {"success": False, "error": str(e)}
            self.log_step(f"DuckDuckGo search failed: {str(e)}", level="ERROR")

        # Test PullMdLoader tool
        self.log_step("Testing PullMdLoader webpage tool")
        try:
            start_time = datetime.now()
            # Test with a simple website
            webpage_tool = ai_service._create_tools()[1]  # Second tool should be fetch_webpage_tool
            webpage_result = webpage_tool.run("https://www.redcross.org")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            test_results["fetch_webpage_tool"] = {
                "success": True, 
                "result": webpage_result[:500] + "..." if len(webpage_result) > 500 else webpage_result,
                "execution_time": execution_time
            }
            performance_metrics["fetch_webpage_tool"] = {
                "execution_time": execution_time,
                "result_length": len(webpage_result)
            }
            self.log_step("PullMdLoader webpage tool successful", {
                "result_length": len(webpage_result),
                "execution_time": execution_time
            })
        except Exception as e:
            test_results["fetch_webpage_tool"] = {"success": False, "error": str(e)}
            self.log_step(f"PullMdLoader webpage tool failed: {str(e)}", level="ERROR")
        
        # Add performance summary
        if performance_metrics:
            total_time = sum(metric["execution_time"] for metric in performance_metrics.values())
            avg_time = total_time / len(performance_metrics)
            test_results["performance_summary"] = {
                "total_execution_time": total_time,
                "average_execution_time": avg_time,
                "tools_tested": len(performance_metrics),
                "successful_tools": len([r for r in test_results.values() if isinstance(r, dict) and r.get("success", False)])
            }
        
        return test_results
    
    def test_with_sample_data(self) -> Dict[str, Any]:
        """Test AI service with sample data."""
        print(f"\n{'='*80}")
        print("🧪 TESTING WITH SAMPLE DATA")
        print(f"{'='*80}")
        
        # Use real data for a well-known organization that can be verified
        sample_data = {
            "name": "Red Cross",
            "description": "Humanitarian organization providing emergency assistance",
            "phone": "1-800-RED-CROSS",
            "email": "info@redcross.org",
            "website": "redcross.org",
            "address1": "431 18th Street NW",
            "city": "Washington",
            "state": "DC",
            "postal_code": "20006"
        }
        
        self.log_step("Using sample data", sample_data)
        
        ai_service = AIReviewService()
        if not ai_service.is_available():
            self.log_step("AI service not available", level="ERROR")
            return {"error": "AI service not available"}
        
        result = self._debug_ai_verification(ai_service, sample_data)
        analysis = self._analyze_results(result, sample_data)
        summary = self._generate_summary(result, analysis)
        
        return {
            "success": True,
            "sample_data": sample_data,
            "verification_result": result,
            "analysis": analysis,
            "summary": summary,
            "debug_log": self.debug_log
        }

    def test_missing_field_recommendations(self) -> Dict[str, Any]:
        """Test AI missing field detection and recommendation system."""
        print(f"\n{'='*80}")
        print(f"🔍 TESTING MISSING FIELD RECOMMENDATIONS")
        print(f"{'='*80}")
        
        # Create test data with intentionally missing fields
        incomplete_data = {
            "name": "Test Organization",
            "description": "A test organization for missing field testing",
            "phone": "",  # Missing
            "email": "",  # Missing
            "website": "",  # Missing
            "address1": "123 Test Street",
            "address2": "",  # Missing
            "city": "Test City",
            "state": "KY",
            "postal_code": "",  # Missing
            "county": "",  # Missing
            "category": "Test Category",
            "service_types": [],
            "hours_of_operation": "",  # Missing
            "is_emergency_service": None,  # Missing
            "is_24_hour_service": None,  # Missing
            "eligibility_requirements": "",  # Missing
            "populations_served": "",  # Missing
            "insurance_accepted": "",  # Missing
            "cost_information": "",  # Missing
            "languages_available": "",  # Missing
            "capacity": "",  # Missing
            "source": "Test",
            "notes": "Test data with missing fields"
        }
        
        self.log_step("Testing missing field recommendations", {
            "resource_name": incomplete_data["name"],
            "scenario": "Resource with intentionally missing fields",
            "missing_fields_count": len([v for v in incomplete_data.values() if not v or v == ""])
        })
        
        try:
            # Initialize AI service
            ai_service = AIReviewService()
            
            if not ai_service.is_available():
                self.log_step("AI service not available", level="ERROR")
                return {"error": "AI service not available"}
            
            # Run verification with incomplete data
            self.log_step("Running AI verification with missing fields")
            result = ai_service.verify_resource_data(incomplete_data)
            
            # Analyze missing field recommendations
            analysis = self._analyze_missing_field_recommendations(result, incomplete_data)
            
            return {
                "success": True,
                "scenario": "missing_field_recommendations",
                "original_data": incomplete_data,
                "verification_result": result,
                "missing_field_analysis": analysis,
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            self.log_step(f"Error in missing field recommendations test: {str(e)}", level="ERROR")
            return {"error": str(e)}
    
    def _analyze_missing_field_recommendations(self, result: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality and effectiveness of missing field recommendations."""
        analysis = {
            "missing_fields_original": 0,
            "missing_fields_detected": 0,
            "recommendations_provided": 0,
            "recommendation_quality": {},
            "field_specific_analysis": {},
            "overall_effectiveness": "unknown"
        }
        
        # Count originally missing fields
        for field, value in original_data.items():
            if not value or value == "" or value is None:
                analysis["missing_fields_original"] += 1
        
        # Analyze missing field recommendations
        if "missing_field_recommendations" in result:
            missing_recs = result["missing_field_recommendations"]
            analysis["recommendations_provided"] = len(missing_recs)
            
            for field, recommendation in missing_recs.items():
                # Analyze recommendation quality
                quality_score = self._assess_recommendation_quality(recommendation)
                analysis["recommendation_quality"][field] = {
                    "recommendation": recommendation,
                    "quality_score": quality_score,
                    "quality_level": self._get_quality_level(quality_score)
                }
                
                analysis["field_specific_analysis"][field] = {
                    "was_missing_originally": not original_data.get(field) or original_data.get(field) == "",
                    "recommendation_provided": True,
                    "recommendation_length": len(recommendation),
                    "has_actionable_content": "call" in recommendation.lower() or "check" in recommendation.lower() or "contact" in recommendation.lower()
                }
        
        # Analyze verification statuses for NOT_FOUND fields
        if "verification_statuses" in result:
            not_found_fields = [field for field, status in result["verification_statuses"].items() if status == "NOT_FOUND"]
            analysis["missing_fields_detected"] = len(not_found_fields)
            
            # Check if NOT_FOUND fields have recommendations
            for field in not_found_fields:
                if field not in analysis["field_specific_analysis"]:
                    analysis["field_specific_analysis"][field] = {
                        "was_missing_originally": not original_data.get(field) or original_data.get(field) == "",
                        "recommendation_provided": False,
                        "status": "NOT_FOUND"
                    }
        
        # Calculate overall effectiveness
        if analysis["missing_fields_original"] > 0:
            detection_rate = analysis["missing_fields_detected"] / analysis["missing_fields_original"]
            recommendation_rate = analysis["recommendations_provided"] / analysis["missing_fields_detected"] if analysis["missing_fields_detected"] > 0 else 0
            
            if detection_rate >= 0.8 and recommendation_rate >= 0.8:
                analysis["overall_effectiveness"] = "excellent"
            elif detection_rate >= 0.6 and recommendation_rate >= 0.6:
                analysis["overall_effectiveness"] = "good"
            elif detection_rate >= 0.4 and recommendation_rate >= 0.4:
                analysis["overall_effectiveness"] = "fair"
            else:
                analysis["overall_effectiveness"] = "poor"
        
        return analysis
    
    def _assess_recommendation_quality(self, recommendation: str) -> float:
        """Assess the quality of a missing field recommendation."""
        score = 0.0
        
        # Length check (longer recommendations tend to be more detailed)
        if len(recommendation) > 50:
            score += 20
        elif len(recommendation) > 25:
            score += 15
        elif len(recommendation) > 10:
            score += 10
        
        # Actionable content check
        actionable_words = ["call", "check", "contact", "visit", "search", "look", "find", "verify"]
        actionable_count = sum(1 for word in actionable_words if word in recommendation.lower())
        score += min(actionable_count * 10, 30)
        
        # Specificity check
        specific_indicators = ["official website", "government", "211", "directly", "specific", "local"]
        specific_count = sum(1 for indicator in specific_indicators if indicator in recommendation.lower())
        score += min(specific_count * 8, 24)
        
        # Professional tone check
        professional_indicators = ["please", "recommend", "suggest", "advise", "consider"]
        professional_count = sum(1 for indicator in professional_indicators if indicator in recommendation.lower())
        score += min(professional_count * 5, 15)
        
        # Clarity check (no excessive jargon)
        if len(recommendation.split()) <= 20:  # Concise
            score += 11
        
        return min(score, 100.0)
    
    def _get_quality_level(self, score: float) -> str:
        """Convert quality score to level."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"
    
    def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics and rate limiting compliance."""
        print(f"\n{'='*80}")
        print(f"⚡ PERFORMANCE METRICS TESTING")
        print(f"{'='*80}")
        
        ai_service = AIReviewService()
        
        if not ai_service.is_available():
            self.log_step("AI service not available for performance testing", level="ERROR")
            return {"error": "AI service not available"}
        
        performance_results = {
            "tool_performance": {},
            "rate_limiting_tests": {},
            "timeout_tests": {},
            "overall_metrics": {}
        }
        
        # Test individual tool performance
        self.log_step("Testing individual tool performance")
        tools = ai_service._create_tools()
        
        for i, tool in enumerate(tools):
            tool_name = tool.name if hasattr(tool, 'name') else f"tool_{i}"
            self.log_step(f"Testing performance for {tool_name}")
            
            # Test multiple iterations to get average performance
            execution_times = []
            success_count = 0
            
            for iteration in range(3):  # Test 3 iterations
                try:
                    start_time = datetime.now()
                    
                    if tool_name == "web_search":
                        result = tool.run("Red Cross services")
                    elif tool_name == "fetch_webpage_tool":
                        result = tool.run("https://www.redcross.org")
                    else:
                        result = tool.run("test")
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    execution_times.append(execution_time)
                    success_count += 1
                    
                    self.log_step(f"{tool_name} iteration {iteration + 1}", {
                        "execution_time": execution_time,
                        "result_length": len(str(result))
                    }, level="DEBUG")
                    
                    # Rate limiting: PullMdLoader has 5 req/sec, 20 req/min limits
                    if tool_name == "fetch_webpage_tool":
                        time.sleep(0.2)  # 200ms delay to respect rate limits
                    
                except Exception as e:
                    self.log_step(f"{tool_name} iteration {iteration + 1} failed: {str(e)}", level="ERROR")
            
            # Calculate performance metrics
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                min_time = min(execution_times)
                max_time = max(execution_times)
                
                performance_results["tool_performance"][tool_name] = {
                    "average_execution_time": avg_time,
                    "min_execution_time": min_time,
                    "max_execution_time": max_time,
                    "success_rate": success_count / 3,
                    "iterations_tested": 3
                }
        
        # Test rate limiting compliance
        self.log_step("Testing rate limiting compliance")
        try:
            webpage_tool = tools[1] if len(tools) > 1 else None  # PullMdLoader tool
            
            if webpage_tool:
                # Test rapid requests to check rate limiting
                rapid_times = []
                for i in range(5):  # Test 5 rapid requests
                    start_time = datetime.now()
                    try:
                        result = webpage_tool.run("https://www.redcross.org")
                        execution_time = (datetime.now() - start_time).total_seconds()
                        rapid_times.append(execution_time)
                    except Exception as e:
                        rapid_times.append(None)
                        self.log_step(f"Rate limit test request {i + 1} failed: {str(e)}", level="WARNING")
                
                performance_results["rate_limiting_tests"]["pullmdloader"] = {
                    "rapid_requests_tested": 5,
                    "successful_requests": len([t for t in rapid_times if t is not None]),
                    "average_time_rapid": sum([t for t in rapid_times if t is not None]) / len([t for t in rapid_times if t is not None]) if any(t is not None for t in rapid_times) else 0,
                    "rate_limiting_observed": any(t is None for t in rapid_times)
                }
        
        except Exception as e:
            self.log_step(f"Rate limiting test failed: {str(e)}", level="ERROR")
        
        # Test timeout handling
        self.log_step("Testing timeout handling")
        try:
            # Test with a potentially slow website
            start_time = datetime.now()
            webpage_tool = tools[1] if len(tools) > 1 else None
            
            if webpage_tool:
                try:
                    result = webpage_tool.run("https://httpstat.us/200?sleep=5000")  # 5 second delay
                    execution_time = (datetime.now() - start_time).total_seconds()
                    performance_results["timeout_tests"]["slow_website"] = {
                        "execution_time": execution_time,
                        "timeout_occurred": execution_time > 30,  # Assume 30s timeout
                        "success": True
                    }
                except Exception as e:
                    performance_results["timeout_tests"]["slow_website"] = {
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "timeout_occurred": True,
                        "success": False,
                        "error": str(e)
                    }
        
        except Exception as e:
            self.log_step(f"Timeout test failed: {str(e)}", level="ERROR")
        
        # Calculate overall metrics
        if performance_results["tool_performance"]:
            all_times = []
            for tool_metrics in performance_results["tool_performance"].values():
                all_times.append(tool_metrics["average_execution_time"])
            
            performance_results["overall_metrics"] = {
                "average_tool_execution_time": sum(all_times) / len(all_times),
                "fastest_tool": min(performance_results["tool_performance"].items(), key=lambda x: x[1]["average_execution_time"])[0],
                "slowest_tool": max(performance_results["tool_performance"].items(), key=lambda x: x[1]["average_execution_time"])[0],
                "total_tools_tested": len(performance_results["tool_performance"]),
                "overall_success_rate": sum(tool["success_rate"] for tool in performance_results["tool_performance"].values()) / len(performance_results["tool_performance"])
            }
        
        return performance_results

    def test_conflicting_sources_scenario(self) -> Dict[str, Any]:
        """Test AI decision-making with conflicting sources scenario."""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING CONFLICTING SOURCES SCENARIO")
        print(f"{'='*80}")
        
        # Create a resource with potentially conflicting information
        conflicting_data = {
            "name": "Community Health Center",
            "description": "Local health clinic providing medical services",
            "phone": "555-123-4567",  # This might conflict with online sources
            "email": "info@communityhealth.org",
            "website": "communityhealth.org",  # Might not be the official site
            "address1": "123 Main Street",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
            "category": "Healthcare",
            "service_types": ["Medical Care", "Dental Care"],
            "source": "Manual Entry",
            "notes": "Information may be outdated or conflicting with online sources"
        }
        
        self.log_step("Testing conflicting sources scenario", {
            "resource_name": conflicting_data["name"],
            "scenario": "Multiple sources with conflicting information"
        })
        
        try:
            # Initialize AI service
            ai_service = AIReviewService()
            
            if not ai_service.is_available():
                self.log_step("AI service not available", level="ERROR")
                return {"error": "AI service not available"}
            
            # Run verification with conflicting data
            self.log_step("Running AI verification with conflicting sources")
            result = ai_service.verify_resource_data(conflicting_data)
            
            # Analyze conflict resolution
            analysis = self._analyze_conflict_resolution(result, conflicting_data)
            
            return {
                "success": True,
                "scenario": "conflicting_sources",
                "original_data": conflicting_data,
                "verification_result": result,
                "conflict_analysis": analysis,
                "execution_time": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            self.log_step(f"Error in conflicting sources test: {str(e)}", level="ERROR")
            return {"error": str(e)}
    
    def _analyze_conflict_resolution(self, result: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well the AI resolved conflicts."""
        analysis = {
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "confidence_distribution": {},
            "decision_quality": "unknown",
            "issues_found": []
        }
        
        # Check for conflicting fields
        if "verification_statuses" in result:
            for field, status in result["verification_statuses"].items():
                if status == "CONFLICTING":
                    analysis["conflicts_detected"] += 1
                    # Check if it was resolved
                    if field in result.get("confidence_scores", {}):
                        confidence = result["confidence_scores"][field]
                        if confidence >= 70:  # Resolved with good confidence
                            analysis["conflicts_resolved"] += 1
        
        # Analyze confidence distribution
        if "confidence_scores" in result:
            for field, score in result["confidence_scores"].items():
                if score >= 95:
                    analysis["confidence_distribution"]["very_high"] = analysis["confidence_distribution"].get("very_high", 0) + 1
                elif score >= 85:
                    analysis["confidence_distribution"]["high"] = analysis["confidence_distribution"].get("high", 0) + 1
                elif score >= 70:
                    analysis["confidence_distribution"]["medium"] = analysis["confidence_distribution"].get("medium", 0) + 1
                elif score >= 50:
                    analysis["confidence_distribution"]["low"] = analysis["confidence_distribution"].get("low", 0) + 1
                else:
                    analysis["confidence_distribution"]["very_low"] = analysis["confidence_distribution"].get("very_low", 0) + 1
        
        # Assess decision quality
        if analysis["conflicts_detected"] > 0:
            resolution_rate = analysis["conflicts_resolved"] / analysis["conflicts_detected"]
            if resolution_rate >= 0.8:
                analysis["decision_quality"] = "excellent"
            elif resolution_rate >= 0.6:
                analysis["decision_quality"] = "good"
            elif resolution_rate >= 0.4:
                analysis["decision_quality"] = "fair"
            else:
                analysis["decision_quality"] = "poor"
        else:
            analysis["decision_quality"] = "no_conflicts"
        
        return analysis


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Debug AI Service CLI Tool")
    parser.add_argument("--resource-id", type=int, help="Resource ID to debug")
    parser.add_argument("--update", action="store_true", help="Actually update the resource (like API process)")
    parser.add_argument("--test-data", action="store_true", help="Test with sample data")
    parser.add_argument("--test-tools", action="store_true", help="Test individual tools")
    parser.add_argument("--test-conflicts", action="store_true", help="Test conflicting sources scenario")
    parser.add_argument("--test-missing-fields", action="store_true", help="Test missing field recommendations")
    parser.add_argument("--test-performance", action="store_true", help="Test performance metrics and rate limiting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file for results")
    
    args = parser.parse_args()
    
    if not any([args.resource_id, args.test_data, args.test_tools, args.test_conflicts, args.test_missing_fields, args.test_performance]):
        parser.print_help()
        return
    
    debugger = AIServiceDebugger(verbose=args.verbose)
    results = {}
    
    if args.resource_id:
        if args.update:
            print("⚠️  WARNING: This will actually update the resource in the database!")
            print("   The resource will be marked as 'needs_review' and changes will be applied.")
            print("   This is the same process as the API auto-verification endpoint.")
            print()
            confirm = input("Are you sure you want to proceed? (yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                results["resource_debug_with_update"] = debugger.debug_resource_verification_with_update(args.resource_id)
            else:
                print("Operation cancelled.")
                return
        else:
            results["resource_debug"] = debugger.debug_resource_verification(args.resource_id)
    
    if args.test_data:
        results["sample_data_test"] = debugger.test_with_sample_data()
    
    if args.test_tools:
        results["tools_test"] = debugger.test_individual_tools()
    
    if args.test_conflicts:
        results["conflicts_test"] = debugger.test_conflicting_sources_scenario()
    
    if args.test_missing_fields:
        results["missing_fields_test"] = debugger.test_missing_field_recommendations()
    
    if args.test_performance:
        results["performance_test"] = debugger.test_performance_metrics()
    
    # Print final summary
    print(f"\n{'='*80}")
    print("📊 DEBUG SUMMARY")
    print(f"{'='*80}")
    
    for test_type, result in results.items():
        if "error" in result:
            print(f"❌ {test_type}: {result['error']}")
        else:
            print(f"✅ {test_type}: Completed successfully")
            if "summary" in result:
                summary = result["summary"]
                print(f"   - Fields verified: {summary.get('total_fields_verified', 0)}")
                print(f"   - Fields with changes: {summary.get('fields_with_changes', 0)}")
                print(f"   - Issues found: {summary.get('issues_found', 0)}")
            elif "conflict_analysis" in result:
                analysis = result["conflict_analysis"]
                print(f"   - Conflicts detected: {analysis.get('conflicts_detected', 0)}")
                print(f"   - Conflicts resolved: {analysis.get('conflicts_resolved', 0)}")
                print(f"   - Decision quality: {analysis.get('decision_quality', 'unknown')}")
            elif "missing_field_analysis" in result:
                analysis = result["missing_field_analysis"]
                print(f"   - Missing fields detected: {analysis.get('missing_fields_detected', 0)}")
                print(f"   - Recommendations provided: {analysis.get('recommendations_provided', 0)}")
                print(f"   - Overall effectiveness: {analysis.get('overall_effectiveness', 'unknown')}")
            elif "performance_summary" in result:
                perf = result["performance_summary"]
                print(f"   - Total execution time: {perf.get('total_execution_time', 0):.2f}s")
                print(f"   - Average execution time: {perf.get('average_execution_time', 0):.2f}s")
                print(f"   - Successful tools: {perf.get('successful_tools', 0)}/{perf.get('tools_tested', 0)}")
            elif "overall_metrics" in result:
                metrics = result["overall_metrics"]
                print(f"   - Average tool execution time: {metrics.get('average_tool_execution_time', 0):.2f}s")
                print(f"   - Fastest tool: {metrics.get('fastest_tool', 'unknown')}")
                print(f"   - Overall success rate: {metrics.get('overall_success_rate', 0):.1%}")
            elif "tool_performance" in result:
                tool_perf = result["tool_performance"]
                print(f"   - Tools tested: {len(tool_perf)}")
                for tool_name, perf in tool_perf.items():
                    print(f"   - {tool_name}: {perf.get('average_execution_time', 0):.2f}s avg, {perf.get('success_rate', 0):.1%} success")
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")
    
    print(f"\n⏱️  Total execution time: {(datetime.now() - debugger.start_time).total_seconds():.2f} seconds")
    print(f"📝 Debug log saved to: ai_debug.log")


if __name__ == "__main__":
    main()
