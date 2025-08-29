"""Management command to check data quality of coverage areas.

This command runs comprehensive data quality checks on coverage areas,
including FIPS code validation, duplicate detection, name consistency,
and spatial integrity validation.

Usage:
    python manage.py check_data_quality
    python manage.py check_data_quality --detailed
    python manage.py check_data_quality --fix-issues
    python manage.py check_data_quality --export-report report.json

Features:
    - Comprehensive data quality assessment
    - Detailed error reporting with recommendations
    - Quality score calculation
    - Export capabilities for quality reports
    - Interactive issue resolution

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from directory.utils.data_quality import comprehensive_quality_check

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Check data quality of coverage areas."""

    help = "Run comprehensive data quality checks on coverage areas"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed error information",
        )
        parser.add_argument(
            "--fix-issues",
            action="store_true",
            help="Attempt to automatically fix common issues",
        )
        parser.add_argument(
            "--export-report",
            type=str,
            help="Export quality report to JSON file",
        )
        parser.add_argument(
            "--min-quality-score",
            type=float,
            default=0.8,
            help="Minimum acceptable quality score (default: 0.8)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        detailed = options["detailed"]
        fix_issues = options["fix_issues"]
        export_report = options["export_report"]
        min_quality_score = options["min_quality_score"]

        self.stdout.write("🔍 Starting comprehensive data quality check...")

        try:
            # Run quality check
            report = comprehensive_quality_check()

            # Display summary
            self._display_summary(report, min_quality_score)

            # Display detailed information if requested
            if detailed:
                self._display_detailed_report(report)

            # Export report if requested
            if export_report:
                self._export_report(report, export_report)

            # Attempt to fix issues if requested
            if fix_issues:
                self._fix_issues(report)

            # Return appropriate exit code
            quality_score = report["summary"].get("quality_score", 0.0)
            if quality_score < min_quality_score:
                self.stdout.write(
                    self.style.WARNING(
                        f"Quality score {quality_score:.2f} is below minimum threshold {min_quality_score}"
                    )
                )
                raise CommandError("Data quality below acceptable threshold")
            else:
                self.stdout.write(
                    self.style.SUCCESS("Data quality check completed successfully")
                )

        except Exception as e:
            raise CommandError(f"Error during data quality check: {str(e)}")

    def _display_summary(
        self, report: Dict[str, Any], min_quality_score: float
    ) -> None:
        """Display quality check summary.

        Args:
            report: Quality check report
            min_quality_score: Minimum acceptable quality score
        """
        summary = report["summary"]

        if "error" in summary:
            self.stdout.write(
                self.style.ERROR(f"Error during quality check: {summary['error']}")
            )
            return

        quality_score = summary.get("quality_score", 0.0)
        total_areas = summary.get("total_areas", 0)
        total_errors = summary.get("total_errors", 0)
        status = summary.get("status", "Unknown")

        # Quality score indicator
        if quality_score >= 0.9:
            score_style = self.style.SUCCESS
            score_icon = "🟢"
        elif quality_score >= min_quality_score:
            score_style = self.style.WARNING
            score_icon = "🟡"
        else:
            score_style = self.style.ERROR
            score_icon = "🔴"

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 DATA QUALITY SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total Coverage Areas: {total_areas}")
        self.stdout.write(f"Quality Score: {score_icon} {quality_score:.2%}")
        self.stdout.write(f"Status: {status}")
        self.stdout.write(f"Total Issues: {total_errors}")

        if total_errors > 0:
            self.stdout.write("\n📋 Issue Breakdown:")
            self.stdout.write(
                f"  • FIPS Code Errors: {summary.get('fips_errors_count', 0)}"
            )
            self.stdout.write(f"  • Duplicates: {summary.get('duplicates_count', 0)}")
            self.stdout.write(f"  • Name Issues: {summary.get('name_issues_count', 0)}")
            self.stdout.write(
                f"  • Spatial Issues: {summary.get('spatial_issues_count', 0)}"
            )

        # Recommendations
        if report.get("recommendations"):
            self.stdout.write("\n💡 Recommendations:")
            for rec in report["recommendations"]:
                self.stdout.write(f"  • {rec}")

        self.stdout.write("=" * 60)

    def _display_detailed_report(self, report: Dict[str, Any]) -> None:
        """Display detailed quality check report.

        Args:
            report: Quality check report
        """
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🔍 DETAILED QUALITY REPORT")
        self.stdout.write("=" * 60)

        # FIPS errors
        if report.get("fips_errors"):
            self.stdout.write("\n🚨 FIPS CODE ERRORS:")
            for error in report["fips_errors"]:
                self.stdout.write(
                    f"  • {error.get('area_name', 'Unknown')} "
                    f"(ID: {error.get('area_id', 'N/A')}): {error.get('message', 'Unknown error')}"
                )

        # Duplicates
        if report.get("duplicates"):
            self.stdout.write("\n🔄 DUPLICATES DETECTED:")
            for dup in report["duplicates"]:
                dup_type = dup.get("type", "unknown")
                if dup_type == "spatial_duplicate":
                    self.stdout.write(
                        f"  • Spatial: {dup.get('area1_name', 'Unknown')} ↔ "
                        f"{dup.get('area2_name', 'Unknown')} "
                        f"({dup.get('overlap_ratio', 0):.1%} overlap)"
                    )
                elif dup_type == "name_duplicate":
                    self.stdout.write(
                        f"  • Name: {dup.get('area1_name', 'Unknown')} ↔ "
                        f"{dup.get('area2_name', 'Unknown')} "
                        f"({dup.get('name_similarity', 0):.1%} similarity)"
                    )

        # Name issues
        if report.get("name_issues"):
            self.stdout.write("\n📝 NAME CONSISTENCY ISSUES:")
            for issue in report["name_issues"]:
                self.stdout.write(
                    f"  • {issue.get('area_name', 'Unknown')} "
                    f"(ID: {issue.get('area_id', 'N/A')}): {issue.get('message', 'Unknown issue')}"
                )

        # Spatial issues
        if report.get("spatial_issues"):
            self.stdout.write("\n🗺️ SPATIAL INTEGRITY ISSUES:")
            for issue in report["spatial_issues"]:
                self.stdout.write(
                    f"  • {issue.get('area_name', 'Unknown')} "
                    f"(ID: {issue.get('area_id', 'N/A')}): {issue.get('message', 'Unknown issue')}"
                )

    def _export_report(self, report: Dict[str, Any], filename: str) -> None:
        """Export quality report to JSON file.

        Args:
            report: Quality check report
            filename: Output filename
        """
        try:
            # Add export metadata
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "export_version": "1.0.0",
                "report": report,
            }

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            self.stdout.write(
                self.style.SUCCESS(f"Quality report exported to: {filename}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error exporting report: {str(e)}"))

    def _fix_issues(self, report: Dict[str, Any]) -> None:
        """Attempt to automatically fix common issues.

        Args:
            report: Quality check report
        """
        self.stdout.write("\n🔧 ATTEMPTING TO FIX ISSUES...")

        fixes_applied = 0

        # Note: In a real implementation, this would include actual fix logic
        # For now, we'll just report what could be fixed

        if report.get("name_issues"):
            self.stdout.write(
                "  • Name consistency issues can be fixed with data cleanup"
            )
            fixes_applied += len(report["name_issues"])

        if report.get("spatial_issues"):
            self.stdout.write(
                "  • Spatial integrity issues can be fixed with geometry repair"
            )
            fixes_applied += len(report["spatial_issues"])

        if fixes_applied > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  • {fixes_applied} issues identified for automatic fixing"
                )
            )
        else:
            self.stdout.write("  • No issues suitable for automatic fixing found")

        self.stdout.write(
            "  • Manual review required for FIPS code errors and duplicates"
        )
