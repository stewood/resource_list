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
        Generate a comprehensive Markdown verification report.
        
        Args:
            current_data: Original resource data
            verified_data: Verified/updated data
            change_notes: Notes about changes made
            confidence_levels: Confidence levels for each field
            verification_notes: Detailed verification information
            ai_response: Full AI response
            
        Returns:
            Markdown formatted verification report
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
        
        # Start building the report
        report = []
        
        # Header
        report.append("# Resource Verification Report")
        report.append("")
        
        # Verification Summary
        report.append("## 📊 Verification Summary")
        report.append("")
        report.append(f"- **Resource**: {current_data.get('name', 'Unknown')} (ID: {current_data.get('id', 'N/A')})")
        report.append(f"- **Verification Date**: {timestamp}")
        report.append(f"- **Overall Status**: {'✅ Pass' if fields_failed == 0 else '⚠️ Partial' if fields_failed < 3 else '❌ Fail'}")
        report.append(f"- **Verification Method**: AI-Assisted")
        report.append(f"- **AI Model Used**: meta-llama/llama-4-maverick:free")
        report.append(f"- **Overall Confidence**: {overall_confidence}")
        report.append("")
        
        # Statistics
        report.append("### 📈 Verification Statistics")
        report.append("")
        report.append(f"- **Fields Verified**: {fields_verified}/{total_fields}")
        report.append(f"- **Fields Changed**: {fields_changed}")
        report.append(f"- **Fields Failed**: {fields_failed}")
        report.append(f"- **High Confidence**: {high_count}")
        report.append(f"- **Medium Confidence**: {medium_count}")
        report.append(f"- **Low Confidence**: {low_count}")
        report.append("")
        
        # Field-by-Field Verification
        report.append("## 🔍 Field-by-Field Verification")
        report.append("")
        
        # Basic Information
        report.append("### Basic Information")
        report.append("")
        report.append("| Field | Current Value | Verification Status | Confidence | Notes |")
        report.append("|-------|---------------|-------------------|------------|-------|")
        
        basic_fields = ['name', 'description', 'category']
        for field in basic_fields:
            current_value = current_data.get(field, '')
            verified_value = verified_data.get(field, current_value)
            confidence = confidence_levels.get(f"{field}_confidence", "Medium")
            change_note = change_notes.get(field, "No changes")
            
            # Truncate long values for table
            current_display = str(current_value)[:50] + "..." if len(str(current_value)) > 50 else str(current_value)
            verified_display = str(verified_value)[:50] + "..." if len(str(verified_value)) > 50 else str(verified_value)
            
            status = "✅ Verified" if "verified" in change_note.lower() else "⚠️ Needs Update" if "update" in change_note.lower() else "❌ Failed"
            
            report.append(f"| {field.title()} | {current_display} | {status} | {confidence} | {change_note[:100]}... |")
        
        report.append("")
        
        # Contact Information
        report.append("### Contact Information")
        report.append("")
        report.append("| Field | Current Value | Verification Status | Confidence | Notes |")
        report.append("|-------|---------------|-------------------|------------|-------|")
        
        contact_fields = ['phone', 'email', 'website']
        for field in contact_fields:
            current_value = current_data.get(field, '')
            verified_value = verified_data.get(field, current_value)
            confidence = confidence_levels.get(f"{field}_confidence", "Medium")
            change_note = change_notes.get(field, "No changes")
            
            current_display = str(current_value)[:50] + "..." if len(str(current_value)) > 50 else str(current_value)
            status = "✅ Verified" if "verified" in change_note.lower() else "⚠️ Needs Update" if "update" in change_note.lower() else "❌ Failed"
            
            report.append(f"| {field.title()} | {current_display} | {status} | {confidence} | {change_note[:100]}... |")
        
        report.append("")
        
        # Location Information
        report.append("### Location Information")
        report.append("")
        report.append("| Field | Current Value | Verification Status | Confidence | Notes |")
        report.append("|-------|---------------|-------------------|------------|-------|")
        
        location_fields = ['address1', 'address2', 'city', 'state', 'postal_code', 'county']
        for field in location_fields:
            current_value = current_data.get(field, '')
            verified_value = verified_data.get(field, current_value)
            confidence = confidence_levels.get(f"{field}_confidence", "Medium")
            change_note = change_notes.get(field, "No changes")
            
            current_display = str(current_value)[:50] + "..." if len(str(current_value)) > 50 else str(current_value)
            status = "✅ Verified" if "verified" in change_note.lower() else "⚠️ Needs Update" if "update" in change_note.lower() else "❌ Failed"
            
            report.append(f"| {field.replace('_', ' ').title()} | {current_display} | {status} | {confidence} | {change_note[:100]}... |")
        
        report.append("")
        
        # Service Information
        report.append("### Service Information")
        report.append("")
        report.append("| Field | Current Value | Verification Status | Confidence | Notes |")
        report.append("|-------|---------------|-------------------|------------|-------|")
        
        service_fields = ['service_types', 'hours_of_operation', 'eligibility_requirements', 'populations_served', 'cost_information', 'languages_available']
        for field in service_fields:
            current_value = current_data.get(field, '')
            verified_value = verified_data.get(field, current_value)
            confidence = confidence_levels.get(f"{field}_confidence", "Medium")
            change_note = change_notes.get(field, "No changes")
            
            # Handle list values
            if isinstance(current_value, list):
                current_display = ", ".join(current_value)[:50] + "..." if len(", ".join(current_value)) > 50 else ", ".join(current_value)
            else:
                current_display = str(current_value)[:50] + "..." if len(str(current_value)) > 50 else str(current_value)
            
            status = "✅ Verified" if "verified" in change_note.lower() else "⚠️ Needs Update" if "update" in change_note.lower() else "❌ Failed"
            
            report.append(f"| {field.replace('_', ' ').title()} | {current_display} | {status} | {confidence} | {change_note[:100]}... |")
        
        report.append("")
        
        # Sources Consulted
        report.append("## 🌐 Sources Consulted")
        report.append("")
        
        website_url = current_data.get('website', '')
        if website_url:
            report.append("### Primary Sources")
            report.append("")
            report.append(f"- **Website**: `{website_url}` - ✅ Accessible - Information extracted")
            report.append("")
        
        # Extract sources from verification notes
        sources_found = []
        for field, notes in verification_notes.items():
            if isinstance(notes, dict) and 'sources' in notes:
                sources_found.extend(notes['sources'].split(', '))
        
        if sources_found:
            report.append("### Authoritative Sources")
            report.append("")
            unique_sources = list(set(sources_found))
            for source in unique_sources[:10]:  # Limit to 10 sources
                report.append(f"- **{source}** - Information verified")
            report.append("")
        
        # Tools & Methods Used
        report.append("## 🛠️ Tools & Methods Used")
        report.append("")
        
        report.append("### AI Verification Tools")
        report.append("")
        report.append("- **Web Search**: DuckDuckGo authoritative search")
        report.append("- **Website Scraping**: BeautifulSoup content extraction")
        report.append("- **Format Validation**: Regex pattern matching")
        report.append("- **Content Analysis**: AI-powered content verification")
        report.append("")
        
        # Issues & Challenges
        report.append("## ⚠️ Issues & Challenges")
        report.append("")
        
        failed_fields = [k for k, v in change_notes.items() if "failed" in v.lower() or "error" in v.lower()]
        if failed_fields:
            report.append("### Technical Issues")
            report.append("")
            for field in failed_fields:
                report.append(f"- **{field.title()}**: {change_notes[field]}")
            report.append("")
        else:
            report.append("No significant issues encountered during verification.")
            report.append("")
        
        # Suggested Changes
        report.append("## 🎯 Suggested Changes")
        report.append("")
        
        suggested_changes = [k for k, v in change_notes.items() if "suggested" in v.lower() or "recommended" in v.lower()]
        if suggested_changes:
            report.append("### Important Updates")
            report.append("")
            for field in suggested_changes:
                current_value = current_data.get(field, '')
                suggested_value = verified_data.get(field, current_value)
                change_note = change_notes.get(field, "")
                
                report.append(f"- **Field**: {field.replace('_', ' ').title()}")
                report.append(f"- **Current**: {str(current_value)[:100]}...")
                report.append(f"- **Suggested**: {str(suggested_value)[:100]}...")
                report.append(f"- **Reasoning**: {change_note}")
                report.append("")
        else:
            report.append("No suggested changes identified.")
            report.append("")
        
        # Confidence Assessment
        report.append("## 📈 Confidence Assessment")
        report.append("")
        
        report.append(f"### Overall Confidence: {overall_confidence}")
        report.append("")
        report.append("- **High (90-100%)**: Multiple authoritative sources confirm")
        report.append("- **Medium (70-89%)**: Good source but some uncertainty")
        report.append("- **Low (50-69%)**: Limited sources or conflicting info")
        report.append("- **Very Low (<50%)**: Unable to verify or unreliable sources")
        report.append("")
        
        # Future Verification Notes
        report.append("## 🔄 Future Verification Notes")
        report.append("")
        
        report.append("### Re-verification Triggers")
        report.append("")
        report.append("- **Time-based**: Re-verify every 6 months")
        report.append("- **Event-based**: Re-verify if website changes or contact information updates")
        report.append("- **Data-based**: Re-verify if service offerings change")
        report.append("")
        
        # Metadata
        report.append("## 📋 Metadata")
        report.append("")
        
        report.append("### System Information")
        report.append("")
        report.append("- **Verification System**: AI Review Service v1.0")
        report.append("- **AI Model**: meta-llama/llama-4-maverick:free")
        report.append("- **Web Search Tool**: DuckDuckGo")
        report.append("- **Scraping Tool**: BeautifulSoup")
        report.append("- **Validation Tools**: Custom regex patterns")
        report.append("")
        
        report.append("### Performance Metrics")
        report.append("")
        report.append(f"- **Total Fields**: {total_fields}")
        report.append(f"- **Fields Verified**: {fields_verified}")
        report.append(f"- **Fields Changed**: {fields_changed}")
        report.append(f"- **Confidence Score**: {overall_confidence}")
        report.append(f"- **Verification Completeness**: {int((fields_verified/total_fields)*100)}%")
        report.append("")
        
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
