#!/usr/bin/env python3
"""
Comprehensive CLI Debugging Tool for AI Service

This tool provides detailed debugging information for the AI review service,
showing all prompts, inputs, outputs, tool calls, and results in real-time.

Usage:
    python debug_ai_service.py --resource-id 123
    python debug_ai_service.py --test-data
    python debug_ai_service.py --test-tools
    python debug_ai_service.py --verbose --resource-id 123
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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
        """Run AI verification with detailed debugging."""
        self.log_step("Calling AI service verify_resource_data method")
        
        try:
            # Capture the AI response
            result = ai_service.verify_resource_data(current_data)
            
            self.log_step("AI verification completed", {
                "has_verified_data": "verified_data" in result,
                "has_change_notes": "change_notes" in result,
                "has_confidence_levels": "confidence_levels" in result,
                "has_verification_notes": "verification_notes" in result
            })
            
            if self.verbose:
                self.log_step("Full AI response", result, level="DEBUG")
            
            return result
            
        except Exception as e:
            self.log_step(f"Error in AI verification: {str(e)}", level="ERROR")
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
        """Test individual AI tools with detailed debugging."""
        print(f"\n{'='*80}")
        print("🔧 TESTING INDIVIDUAL AI TOOLS")
        print(f"{'='*80}")
        
        ai_service = AIReviewService()
        
        if not ai_service.is_available():
            self.log_step("AI service not available for tool testing", level="ERROR")
            return {"error": "AI service not available"}
        
        test_results = {}
        
                # Test phone verification
        self.log_step("Testing phone verification tool")
        try:
            # Access the underlying function and call it directly
            phone_func = ai_service._verify_phone_tool.func
            phone_result = phone_func(ai_service, phone="555-123-4567")
            test_results["phone"] = {"success": True, "result": phone_result}
            self.log_step("Phone verification successful", {"result": phone_result})
        except Exception as e:
            test_results["phone"] = {"success": False, "error": str(e)}
            self.log_step(f"Phone verification failed: {str(e)}", level="ERROR")

        # Test email verification
        self.log_step("Testing email verification tool")
        try:
            email_func = ai_service._verify_email_tool.func
            email_result = email_func(ai_service, email="test@example.com")
            test_results["email"] = {"success": True, "result": email_result}
            self.log_step("Email verification successful", {"result": email_result})
        except Exception as e:
            test_results["email"] = {"success": False, "error": str(e)}
            self.log_step(f"Email verification failed: {str(e)}", level="ERROR")

        # Test website verification
        self.log_step("Testing website verification tool")
        try:
            website_func = ai_service._verify_website_tool.func
            website_result = website_func(ai_service, website="https://example.com")
            test_results["website"] = {"success": True, "result": website_result}
            self.log_step("Website verification successful", {"result": website_result})
        except Exception as e:
            test_results["website"] = {"success": False, "error": str(e)}
            self.log_step(f"Website verification failed: {str(e)}", level="ERROR")

        # Test address verification
        self.log_step("Testing address verification tool")
        try:
            address_func = ai_service._verify_address_tool.func
            address_result = address_func(ai_service, address="123 Test Street, Test City, KY 12345")
            test_results["address"] = {"success": True, "result": address_result}
            self.log_step("Address verification successful", {"result": address_result})
        except Exception as e:
            test_results["address"] = {"success": False, "error": str(e)}
            self.log_step(f"Address verification failed: {str(e)}", level="ERROR")

        # Test web search tool
        self.log_step("Testing web search tool")
        try:
            search_func = ai_service._authoritative_web_search_tool.func
            search_result = search_func(ai_service, query="Kentucky Department of Health")
            test_results["web_search"] = {"success": True, "result": search_result[:500] + "..." if len(search_result) > 500 else search_result}
            self.log_step("Web search successful", {"result_length": len(search_result)})
        except Exception as e:
            test_results["web_search"] = {"success": False, "error": str(e)}
            self.log_step(f"Web search failed: {str(e)}", level="ERROR")

        # Test service discovery tool
        self.log_step("Testing service discovery tool")
        try:
            discovery_func = ai_service._discover_services_tool.func
            service_discovery_result = discovery_func(ai_service, website_url="https://www.redbirdky.org")
            test_results["service_discovery"] = {"success": True, "result": service_discovery_result[:500] + "..." if len(service_discovery_result) > 500 else service_discovery_result}
            self.log_step("Service discovery successful", {"result_length": len(service_discovery_result)})
        except Exception as e:
            test_results["service_discovery"] = {"success": False, "error": str(e)}
            self.log_step(f"Service discovery failed: {str(e)}", level="ERROR")

        # Test service details extraction tool
        self.log_step("Testing service details extraction tool")
        try:
            # Access the underlying function and call it directly
            details_func = ai_service._extract_service_details_tool.func
            service_details_result = details_func(
                ai_service,
                website_url="https://www.redbirdky.org", 
                service_name="food assistance"
            )
            test_results["service_details"] = {"success": True, "result": service_details_result[:500] + "..." if len(service_details_result) > 500 else service_details_result}
            self.log_step("Service details extraction successful", {"result_length": len(service_details_result)})
        except Exception as e:
            test_results["service_details"] = {"success": False, "error": str(e)}
            self.log_step(f"Service details extraction failed: {str(e)}", level="ERROR")
        
        return test_results
    
    def test_with_sample_data(self) -> Dict[str, Any]:
        """Test AI service with sample data."""
        print(f"\n{'='*80}")
        print("🧪 TESTING WITH SAMPLE DATA")
        print(f"{'='*80}")
        
        sample_data = {
            "name": "Kentucky Department of Health",
            "description": "State health department services",
            "phone": "5025551234",
            "email": "info@ky.gov",
            "website": "ky.gov",
            "address1": "275 E Main St",
            "city": "Frankfort",
            "state": "KY",
            "postal_code": "40601"
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


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Debug AI Service CLI Tool")
    parser.add_argument("--resource-id", type=int, help="Resource ID to debug")
    parser.add_argument("--test-data", action="store_true", help="Test with sample data")
    parser.add_argument("--test-tools", action="store_true", help="Test individual tools")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file for results")
    
    args = parser.parse_args()
    
    if not any([args.resource_id, args.test_data, args.test_tools]):
        parser.print_help()
        return
    
    debugger = AIServiceDebugger(verbose=args.verbose)
    results = {}
    
    if args.resource_id:
        results["resource_debug"] = debugger.debug_resource_verification(args.resource_id)
    
    if args.test_data:
        results["sample_data_test"] = debugger.test_with_sample_data()
    
    if args.test_tools:
        results["tools_test"] = debugger.test_individual_tools()
    
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
    
    # Save results to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")
    
    print(f"\n⏱️  Total execution time: {(datetime.now() - debugger.start_time).total_seconds():.2f} seconds")
    print(f"📝 Debug log saved to: ai_debug.log")


if __name__ == "__main__":
    main()
