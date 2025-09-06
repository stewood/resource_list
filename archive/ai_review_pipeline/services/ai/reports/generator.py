"""
AI Report Generator Module

This module handles generation of verification reports for the AI Review Service.
Responsible for creating comprehensive Markdown reports with verification results.
"""

import re
from typing import Dict, Any, List
from datetime import datetime


class ReportGenerator:
    """
    Report generation functionality for AI verification results.
    
    This class handles creating comprehensive verification reports,
    formatting data for display, and generating statistics.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        pass
    
    def _generate_verification_report(self, current_data: Dict[str, Any], verified_data: Dict[str, Any], 
                                    change_notes: Dict[str, str], confidence_levels: Dict[str, str], 
                                    verification_notes: Dict[str, Any], ai_response: str) -> str:
        """
        Generate a concise Markdown verification report.
        
        Args:
            current_data: Original resource data
            verified_data: Verified/updated data
            change_notes: Notes about changes made
            confidence_levels: Confidence levels for each field
            verification_notes: Detailed verification information
            ai_response: Full AI response
            
        Returns:
            Concise Markdown formatted verification report
        """
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Calculate overall confidence
        confidence_values = [v for v in confidence_levels.values() if isinstance(v, str)]
        high_count = sum(1 for v in confidence_values if "High" in v)
        medium_count = sum(1 for v in confidence_values if "Medium" in v)
        low_count = sum(1 for v in confidence_values if "Low" in v)
        
        total_fields = len(confidence_values)
        overall_confidence = "High" if high_count / total_fields > 0.7 else "Medium" if medium_count / total_fields > 0.3 else "Low"
        
        # Calculate verification statistics
        fields_verified = len([k for k, v in change_notes.items() if "verified" in v.lower() or "updated" in v.lower()])
        fields_changed = len([k for k, v in change_notes.items() if "updated" in v.lower() or "suggested" in v.lower()])
        fields_failed = len([k for k, v in change_notes.items() if "failed" in v.lower() or "error" in v.lower()])
        
        # Start building the concise report
        report = []
        
        # Header
        report.append("# AI Verification Report")
        report.append(f"**{current_data.get('name', 'Unknown Resource')}** - {timestamp}")
        report.append("")
        
        # Quick Summary
        report.append("## 📊 Summary")
        report.append("")
        status_emoji = "✅" if fields_failed == 0 else "⚠️" if fields_failed < 3 else "❌"
        report.append(f"- **Status**: {status_emoji} {'Pass' if fields_failed == 0 else 'Partial' if fields_failed < 3 else 'Fail'}")
        report.append(f"- **Confidence**: {overall_confidence}")
        report.append(f"- **Fields Verified**: {fields_verified}/{total_fields}")
        report.append(f"- **Fields Changed**: {fields_changed}")
        report.append("")
        
        # Key Changes (only show if there are changes)
        if fields_changed > 0:
            report.append("## 🔄 Key Changes")
            report.append("")
            # Define valid fields that can be changed
            valid_fields = {
                'name', 'description', 'category', 'phone', 'email', 'website',
                'address1', 'address2', 'city', 'state', 'postal_code', 'county',
                'service_types', 'hours_of_operation', 'eligibility_requirements',
                'populations_served', 'cost_information', 'languages_available',
                'is_emergency_service', 'is_24_hour_service', 'insurance_accepted',
                'capacity', 'source', 'notes'
            }
            
            for field, note in change_notes.items():
                if "updated" in note.lower() or "suggested" in note.lower():
                    # Only show changes for valid fields
                    if field in valid_fields:
                        current_value = current_data.get(field, '')
                        suggested_value = verified_data.get(field, current_value)
                        if current_value != suggested_value:
                            report.append(f"- **{field.replace('_', ' ').title()}**: `{str(current_value)[:30]}` → `{str(suggested_value)[:30]}`")
            report.append("")
        
        # Service Areas Summary
        verified_service_areas = verified_data.get('service_areas', {})
        if verified_service_areas:
            discovered_areas = verified_service_areas.get('discovered_areas', [])
            if discovered_areas:
                report.append("## 🗺️ Service Areas")
                report.append("")
                for area in discovered_areas:
                    if isinstance(area, dict):
                        area_name = area.get('area_name', 'Unknown')
                        validation_status = area.get('validation_status', 'UNKNOWN')
                        confidence_score = area.get('confidence_score', 0)
                        
                        if validation_status == 'VALID':
                            report.append(f"- ✅ **{area_name}** ({confidence_score}% confidence)")
                        else:
                            report.append(f"- ❌ **{area_name}** (invalid/out of scope)")
                report.append("")
        
        # Issues (only show if there are issues)
        failed_fields = [k for k, v in change_notes.items() if "failed" in v.lower() or "error" in v.lower()]
        if failed_fields:
            report.append("## ⚠️ Issues")
            report.append("")
            for field in failed_fields[:3]:  # Limit to 3 issues
                report.append(f"- **{field.replace('_', ' ').title()}**: {change_notes[field][:100]}...")
            report.append("")
        
        # Sources (simplified)
        website_url = current_data.get('website', '')
        if website_url:
            report.append("## 🌐 Sources")
            report.append("")
            report.append(f"- **Primary**: {website_url}")
            report.append("")
        
        # Footer
        report.append("---")
        report.append(f"*Generated by AI Review Service v1.0 using meta-llama/llama-4-maverick:free*")
        
        return "\n".join(report)
    
    def _format_verification_summary(self, current_data: Dict[str, Any], verified_data: Dict[str, Any], 
                                   change_notes: Dict[str, str]) -> str:
        """
        Generate a brief verification summary.
        
        Args:
            current_data: Original resource data
            verified_data: Verified/updated data
            change_notes: Notes about changes made
            
        Returns:
            Brief summary of verification results
        """
        summary = []
        summary.append(f"## Verification Summary for {current_data.get('name', 'Unknown Resource')}")
        summary.append("")
        
        # Count changes
        fields_changed = len([k for k, v in change_notes.items() if "suggested" in v.lower() or "updated" in v.lower()])
        fields_verified = len([k for k, v in change_notes.items() if "verified" in v.lower()])
        
        summary.append(f"- **Fields Verified**: {fields_verified}")
        summary.append(f"- **Fields Changed**: {fields_changed}")
        summary.append(f"- **Total Fields**: {len(current_data)}")
        summary.append("")
        
        # List key changes
        if fields_changed > 0:
            summary.append("### Key Changes:")
            summary.append("")
            for field, note in change_notes.items():
                if "suggested" in note.lower() or "updated" in note.lower():
                    current_value = current_data.get(field, '')
                    suggested_value = verified_data.get(field, current_value)
                    summary.append(f"- **{field.replace('_', ' ').title()}**: {str(current_value)[:50]} → {str(suggested_value)[:50]}")
            summary.append("")
        
        return "\n".join(summary)
    
    def _generate_statistics_report(self, confidence_levels: Dict[str, str], change_notes: Dict[str, str]) -> str:
        """
        Generate statistics report from verification data.
        
        Args:
            confidence_levels: Confidence levels for each field
            change_notes: Notes about changes made
            
        Returns:
            Statistics report as string
        """
        stats = []
        stats.append("## 📊 Verification Statistics")
        stats.append("")
        
        # Calculate statistics
        confidence_values = [v for v in confidence_levels.values() if isinstance(v, str)]
        high_count = sum(1 for v in confidence_values if "High" in v)
        medium_count = sum(1 for v in confidence_values if "Medium" in v)
        low_count = sum(1 for v in confidence_values if "Low" in v)
        
        fields_verified = len([k for k, v in change_notes.items() if "verified" in v.lower()])
        fields_changed = len([k for k, v in change_notes.items() if "suggested" in v.lower() or "updated" in v.lower()])
        fields_failed = len([k for k, v in change_notes.items() if "failed" in v.lower() or "error" in v.lower()])
        
        total_fields = len(confidence_values)
        
        stats.append(f"- **Total Fields**: {total_fields}")
        stats.append(f"- **Fields Verified**: {fields_verified}")
        stats.append(f"- **Fields Changed**: {fields_changed}")
        stats.append(f"- **Fields Failed**: {fields_failed}")
        stats.append(f"- **High Confidence**: {high_count}")
        stats.append(f"- **Medium Confidence**: {medium_count}")
        stats.append(f"- **Low Confidence**: {low_count}")
        stats.append("")
        
        # Calculate percentages
        if total_fields > 0:
            verification_rate = (fields_verified / total_fields) * 100
            change_rate = (fields_changed / total_fields) * 100
            high_confidence_rate = (high_count / total_fields) * 100
            
            stats.append(f"- **Verification Rate**: {verification_rate:.1f}%")
            stats.append(f"- **Change Rate**: {change_rate:.1f}%")
            stats.append(f"- **High Confidence Rate**: {high_confidence_rate:.1f}%")
            stats.append("")
        
        return "\n".join(stats)
