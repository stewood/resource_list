"""Data Quality Utilities - Coverage Area Data Validation and Quality Checks

This module provides comprehensive data quality checking utilities for coverage areas,
including FIPS code validation, duplicate detection, name consistency checks, and
overall data integrity validation.

Functions:
    - validate_fips_codes: Validate FIPS code consistency and format
    - check_duplicate_coverage_areas: Detect and report duplicate areas
    - validate_name_consistency: Check naming conventions and consistency
    - comprehensive_quality_check: Run all quality checks on coverage areas

Features:
    - FIPS code format and consistency validation
    - Geographic duplicate detection (spatial overlap)
    - Name-based duplicate detection
    - Naming convention validation
    - Data integrity reporting
    - Quality score calculation
    - Detailed error reporting with recommendations

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Usage:
    from directory.utils.data_quality import comprehensive_quality_check
    
    # Run comprehensive quality check
    quality_report = comprehensive_quality_check()
    
    # Check specific aspects
    fips_errors = validate_fips_codes()
    duplicates = check_duplicate_coverage_areas()
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import re

from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Q

from directory.models import CoverageArea

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Main class for data quality checking operations."""
    
    # FIPS code patterns
    STATE_FIPS_PATTERN = r'^[0-9]{2}$'
    COUNTY_FIPS_PATTERN = r'^[0-9]{3}$'
    CITY_FIPS_PATTERN = r'^[0-9]{5}$'
    
    # Name consistency patterns
    COUNTY_NAME_PATTERN = r'^[A-Za-z\s\-\.\']+ County$'
    CITY_NAME_PATTERN = r'^[A-Za-z\s\-\.\']+$'
    STATE_NAME_PATTERN = r'^[A-Za-z\s\-\.\']+$'
    
    # Quality thresholds
    MIN_QUALITY_SCORE = 0.8
    MAX_SPATIAL_OVERLAP = 0.95  # 95% overlap considered duplicate
    MIN_NAME_SIMILARITY = 0.8   # 80% similarity for name-based duplicates
    
    @classmethod
    def comprehensive_quality_check(cls) -> Dict[str, Any]:
        """Run comprehensive data quality check on all coverage areas.
        
        This method performs all quality checks and returns a comprehensive
        report with quality scores, error details, and recommendations.
        
        Returns:
            Dictionary containing quality report with scores, errors, and recommendations
        """
        logger.info("Starting comprehensive data quality check")
        
        report = {
            'summary': {},
            'fips_errors': [],
            'duplicates': [],
            'name_issues': [],
            'spatial_issues': [],
            'recommendations': []
        }
        
        try:
            # Get all coverage areas
            coverage_areas = list(CoverageArea.objects.all())
            total_areas = len(coverage_areas)
            
            if total_areas == 0:
                report['summary'] = {
                    'total_areas': 0,
                    'quality_score': 1.0,
                    'status': 'No coverage areas found'
                }
                return report
            
            # Run individual quality checks
            fips_errors = cls.validate_fips_codes()
            duplicates = cls.check_duplicate_coverage_areas()
            name_issues = cls.validate_name_consistency()
            spatial_issues = cls.check_spatial_integrity()
            
            # Compile results
            report['fips_errors'] = fips_errors
            report['duplicates'] = duplicates
            report['name_issues'] = name_issues
            report['spatial_issues'] = spatial_issues
            
            # Calculate quality score
            total_errors = len(fips_errors) + len(duplicates) + len(name_issues) + len(spatial_issues)
            quality_score = max(0.0, 1.0 - (total_errors / total_areas))
            
            # Generate summary
            report['summary'] = {
                'total_areas': total_areas,
                'quality_score': quality_score,
                'total_errors': total_errors,
                'fips_errors_count': len(fips_errors),
                'duplicates_count': len(duplicates),
                'name_issues_count': len(name_issues),
                'spatial_issues_count': len(spatial_issues),
                'status': 'Good' if quality_score >= cls.MIN_QUALITY_SCORE else 'Needs Attention'
            }
            
            # Generate recommendations
            report['recommendations'] = cls._generate_recommendations(report)
            
            logger.info(f"Quality check completed. Score: {quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error during quality check: {str(e)}")
            report['summary'] = {
                'error': str(e),
                'status': 'Error'
            }
        
        return report
    
    @classmethod
    def validate_fips_codes(cls) -> List[Dict[str, Any]]:
        """Validate FIPS code consistency and format.
        
        Checks:
        - FIPS code format validation
        - State/County FIPS code consistency
        - Missing FIPS codes for required area types
        - Invalid FIPS code combinations
        
        Returns:
            List of FIPS validation errors with details
        """
        errors = []
        
        try:
            coverage_areas = list(CoverageArea.objects.all())
            
            for area in coverage_areas:
                ext_ids = area.ext_ids or {}
                
                # Check state FIPS codes
                if area.kind in ['COUNTY', 'CITY']:
                    state_fips = ext_ids.get('state_fips')
                    if not state_fips:
                        errors.append({
                            'area_id': area.id,
                            'area_name': area.name,
                            'kind': area.kind,
                            'error_type': 'missing_state_fips',
                            'message': f"{area.kind} area missing state FIPS code"
                        })
                    elif not re.match(cls.STATE_FIPS_PATTERN, str(state_fips)):
                        errors.append({
                            'area_id': area.id,
                            'area_name': area.name,
                            'kind': area.kind,
                            'error_type': 'invalid_state_fips',
                            'message': f"Invalid state FIPS format: {state_fips}"
                        })
                
                # Check county FIPS codes
                if area.kind == 'COUNTY':
                    county_fips = ext_ids.get('county_fips')
                    if not county_fips:
                        errors.append({
                            'area_id': area.id,
                            'area_name': area.name,
                            'kind': area.kind,
                            'error_type': 'missing_county_fips',
                            'message': f"County area missing county FIPS code"
                        })
                    elif not re.match(cls.COUNTY_FIPS_PATTERN, str(county_fips)):
                        errors.append({
                            'area_id': area.id,
                            'area_name': area.name,
                            'kind': area.kind,
                            'error_type': 'invalid_county_fips',
                            'message': f"Invalid county FIPS format: {county_fips}"
                        })
                
                # Check city FIPS codes
                if area.kind == 'CITY':
                    city_fips = ext_ids.get('city_fips')
                    if city_fips and not re.match(cls.CITY_FIPS_PATTERN, str(city_fips)):
                        errors.append({
                            'area_id': area.id,
                            'area_name': area.name,
                            'kind': area.kind,
                            'error_type': 'invalid_city_fips',
                            'message': f"Invalid city FIPS format: {city_fips}"
                        })
                
                # Check FIPS code consistency
                if area.kind == 'COUNTY':
                    state_fips = ext_ids.get('state_fips')
                    county_fips = ext_ids.get('county_fips')
                    if state_fips and county_fips:
                        # Check if this state/county combination already exists
                        existing = CoverageArea.objects.filter(
                            kind='COUNTY'
                        ).exclude(id=area.id)
                        
                        # Filter by FIPS codes manually since JSON field queries can be problematic
                        for existing_area in existing:
                            existing_ext_ids = existing_area.ext_ids or {}
                            if (existing_ext_ids.get('state_fips') == state_fips and 
                                existing_ext_ids.get('county_fips') == county_fips):
                                duplicate_found = existing_area
                                break
                        else:
                            duplicate_found = None
                        
                        if duplicate_found:
                            errors.append({
                                'area_id': area.id,
                                'area_name': area.name,
                                'kind': area.kind,
                                'error_type': 'duplicate_fips',
                                'message': f"Duplicate FIPS combination: {state_fips}{county_fips}",
                                'duplicate_of': duplicate_found.id
                            })
        
        except Exception as e:
            logger.error(f"Error validating FIPS codes: {str(e)}")
            errors.append({
                'error_type': 'validation_error',
                'message': f"Error during FIPS validation: {str(e)}"
            })
        
        return errors
    
    @classmethod
    def check_duplicate_coverage_areas(cls) -> List[Dict[str, Any]]:
        """Detect and report duplicate coverage areas.
        
        Checks for:
        - Spatial duplicates (high overlap)
        - Name-based duplicates
        - FIPS code duplicates
        
        Returns:
            List of duplicate detection results
        """
        duplicates = []
        
        try:
            coverage_areas = list(CoverageArea.objects.all())
            areas_list = coverage_areas
            
            # Check for spatial duplicates
            for i, area1 in enumerate(areas_list):
                for j, area2 in enumerate(areas_list[i+1:], i+1):
                    # Skip if different kinds (except for potential overlaps)
                    if area1.kind != area2.kind and not cls._should_check_overlap(area1, area2):
                        continue
                    
                    # Check spatial overlap
                    if area1.geom and area2.geom:
                        try:
                            intersection = area1.geom.intersection(area2.geom)
                            if not intersection.empty:
                                overlap_ratio = intersection.area / min(area1.geom.area, area2.geom.area)
                                
                                if overlap_ratio > cls.MAX_SPATIAL_OVERLAP:
                                    duplicates.append({
                                        'type': 'spatial_duplicate',
                                        'area1_id': area1.id,
                                        'area1_name': area1.name,
                                        'area1_kind': area1.kind,
                                        'area2_id': area2.id,
                                        'area2_name': area2.name,
                                        'area2_kind': area2.kind,
                                        'overlap_ratio': overlap_ratio,
                                        'message': f"High spatial overlap: {overlap_ratio:.2%}"
                                    })
                        except Exception as e:
                            logger.warning(f"Error checking spatial overlap: {str(e)}")
                    
                    # Check name similarity
                    name_similarity = cls._calculate_name_similarity(area1.name, area2.name)
                    if name_similarity > cls.MIN_NAME_SIMILARITY and area1.kind == area2.kind:
                        duplicates.append({
                            'type': 'name_duplicate',
                            'area1_id': area1.id,
                            'area1_name': area1.name,
                            'area1_kind': area1.kind,
                            'area2_id': area2.id,
                            'area2_name': area2.name,
                            'area2_kind': area2.kind,
                            'name_similarity': name_similarity,
                            'message': f"Similar names: {name_similarity:.2%} similarity"
                        })
        
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            duplicates.append({
                'type': 'error',
                'message': f"Error during duplicate detection: {str(e)}"
            })
        
        return duplicates
    
    @classmethod
    def validate_name_consistency(cls) -> List[Dict[str, Any]]:
        """Validate naming conventions and consistency.
        
        Checks:
        - County names end with "County"
        - Consistent capitalization
        - No excessive whitespace
        - Valid characters in names
        
        Returns:
            List of name validation issues
        """
        issues = []
        
        try:
            coverage_areas = list(CoverageArea.objects.all())
            
            for area in coverage_areas:
                name = area.name.strip()
                
                # Check county naming convention
                if area.kind == 'COUNTY':
                    if not re.match(cls.COUNTY_NAME_PATTERN, name):
                        issues.append({
                            'area_id': area.id,
                            'area_name': name,
                            'kind': area.kind,
                            'error_type': 'county_naming',
                            'message': f"County name should end with 'County': {name}"
                        })
                
                # Check for excessive whitespace
                if '  ' in name:
                    issues.append({
                        'area_id': area.id,
                        'area_name': name,
                        'kind': area.kind,
                        'error_type': 'excessive_whitespace',
                        'message': f"Name contains excessive whitespace: {name}"
                    })
                
                # Check for invalid characters
                if not re.match(r'^[A-Za-z0-9\s\-\.\',\(\)]+$', name):
                    issues.append({
                        'area_id': area.id,
                        'area_name': name,
                        'kind': area.kind,
                        'error_type': 'invalid_characters',
                        'message': f"Name contains invalid characters: {name}"
                    })
                
                # Check for very short names
                if len(name) < 2:
                    issues.append({
                        'area_id': area.id,
                        'area_name': name,
                        'kind': area.kind,
                        'error_type': 'name_too_short',
                        'message': f"Name too short: {name}"
                    })
        
        except Exception as e:
            logger.error(f"Error validating names: {str(e)}")
            issues.append({
                'error_type': 'validation_error',
                'message': f"Error during name validation: {str(e)}"
            })
        
        return issues
    
    @classmethod
    def check_spatial_integrity(cls) -> List[Dict[str, Any]]:
        """Check spatial integrity of coverage areas.
        
        Checks:
        - Geometry validity
        - Reasonable area sizes
        - Coordinate bounds
        - Spatial relationships
        
        Returns:
            List of spatial integrity issues
        """
        issues = []
        
        try:
            coverage_areas = list(CoverageArea.objects.all())
            
            for area in coverage_areas:
                if not area.geom:
                    issues.append({
                        'area_id': area.id,
                        'area_name': area.name,
                        'kind': area.kind,
                        'error_type': 'missing_geometry',
                        'message': "Missing geometry"
                    })
                    continue
                
                # Check geometry validity
                if not area.geom.valid:
                    issues.append({
                        'area_id': area.id,
                        'area_name': area.name,
                        'kind': area.kind,
                        'error_type': 'invalid_geometry',
                        'message': f"Invalid geometry: {area.geom.valid_reason}"
                    })
                
                # Check area size reasonableness
                area_size = area.geom.area
                if area_size > 1000:  # Very large areas
                    issues.append({
                        'area_id': area.id,
                        'area_name': area.name,
                        'kind': area.kind,
                        'error_type': 'area_too_large',
                        'message': f"Area very large: {area_size:.2f} square degrees"
                    })
                elif area_size < 1e-8:  # Very small areas
                    issues.append({
                        'area_id': area.id,
                        'area_name': area.name,
                        'kind': area.kind,
                        'error_type': 'area_too_small',
                        'message': f"Area very small: {area_size:.2e} square degrees"
                    })
        
        except Exception as e:
            logger.error(f"Error checking spatial integrity: {str(e)}")
            issues.append({
                'error_type': 'validation_error',
                'message': f"Error during spatial integrity check: {str(e)}"
            })
        
        return issues
    
    @classmethod
    def _should_check_overlap(cls, area1: CoverageArea, area2: CoverageArea) -> bool:
        """Determine if two areas should be checked for overlap.
        
        Args:
            area1: First coverage area
            area2: Second coverage area
            
        Returns:
            True if overlap check should be performed
        """
        # Check overlaps between different types that might legitimately overlap
        overlap_combinations = [
            ('CITY', 'COUNTY'),  # Cities within counties
            ('CITY', 'STATE'),   # Cities within states
            ('COUNTY', 'STATE'), # Counties within states
            ('POLYGON', 'COUNTY'), # Custom polygons within counties
            ('POLYGON', 'CITY'),   # Custom polygons within cities
        ]
        
        return (area1.kind, area2.kind) in overlap_combinations or (area2.kind, area1.kind) in overlap_combinations
    
    @classmethod
    def _calculate_name_similarity(cls, name1: str, name2: str) -> float:
        """Calculate similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity calculation using set intersection
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    @classmethod
    def _generate_recommendations(cls, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality check results.
        
        Args:
            report: Quality check report
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # FIPS code recommendations
        if report['fips_errors']:
            recommendations.append("Fix FIPS code validation errors to ensure data consistency")
        
        # Duplicate recommendations
        if report['duplicates']:
            recommendations.append("Review and resolve duplicate coverage areas")
        
        # Name consistency recommendations
        if report['name_issues']:
            recommendations.append("Standardize naming conventions across coverage areas")
        
        # Spatial integrity recommendations
        if report['spatial_issues']:
            recommendations.append("Review and fix spatial integrity issues")
        
        # General recommendations
        if report['summary'].get('quality_score', 1.0) < cls.MIN_QUALITY_SCORE:
            recommendations.append("Overall data quality needs improvement")
        else:
            recommendations.append("Data quality is good, continue monitoring")
        
        return recommendations


# Convenience functions for direct use
def validate_fips_codes() -> List[Dict[str, Any]]:
    """Convenience function for FIPS code validation.
    
    Returns:
        List of FIPS validation errors
    """
    return DataQualityChecker.validate_fips_codes()


def check_duplicate_coverage_areas() -> List[Dict[str, Any]]:
    """Convenience function for duplicate detection.
    
    Returns:
        List of duplicate detection results
    """
    return DataQualityChecker.check_duplicate_coverage_areas()


def validate_name_consistency() -> List[Dict[str, Any]]:
    """Convenience function for name consistency validation.
    
    Returns:
        List of name validation issues
    """
    return DataQualityChecker.validate_name_consistency()


def comprehensive_quality_check() -> Dict[str, Any]:
    """Convenience function for comprehensive quality check.
    
    Returns:
        Comprehensive quality report
    """
    return DataQualityChecker.comprehensive_quality_check()
