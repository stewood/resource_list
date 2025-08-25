"""Geometry processing utilities for coverage areas.

This module provides utilities for processing, validating, and optimizing
geometric data used in coverage areas. It includes functions for:

- Geometry simplification for display optimization
- Winding order correction for consistent polygon orientation
- Multipart geometry handling and normalization
- Coordinate validation and transformation
- Performance optimization for large geometries

Features:
    - Topology-preserving simplification
    - Adaptive simplification based on geometry size
    - Polygon hole handling
    - Self-intersection detection and repair
    - Memory-efficient processing for large datasets

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0
"""

import logging
from typing import List, Optional, Tuple, Union
from decimal import Decimal
import math

from django.conf import settings

# Only import GIS modules if GIS is enabled
if getattr(settings, 'GIS_ENABLED', False):
    from django.contrib.gis.geos import (
        GEOSGeometry, 
        Point, 
        Polygon, 
        MultiPolygon,
        LinearRing
    )
    from django.contrib.gis.geos.error import GEOSException
else:
    # Create dummy classes for when GIS is disabled
    class GEOSGeometry:
        pass
    
    class Point:
        pass
    
    class Polygon:
        pass
    
    class MultiPolygon:
        pass
    
    class LinearRing:
        pass
    
    class GEOSException(Exception):
        pass

logger = logging.getLogger(__name__)


class GeometryProcessor:
    """Main class for geometry processing operations."""
    
    # Default tolerances for different operations
    DEFAULT_SIMPLIFY_TOLERANCE = 0.001  # ~100m at equator
    DISPLAY_SIMPLIFY_TOLERANCE = 0.01   # ~1km at equator for display
    MIN_SIMPLIFY_TOLERANCE = 0.0001     # Minimum tolerance to prevent over-simplification
    MAX_VERTICES_DISPLAY = 1000         # Maximum vertices for display geometries
    MAX_VERTICES_STORAGE = 10000        # Maximum vertices for storage
    
    # Validation limits
    MIN_VERTICES_POLYGON = 4            # Minimum vertices for a valid polygon (including closure)
    MAX_VERTICES_POLYGON = 50000        # Maximum vertices for a single polygon
    MIN_AREA_SQ_DEGREES = 1e-10         # Minimum area in square degrees (very small but not zero)
    MAX_AREA_SQ_DEGREES = 10000         # Maximum area in square degrees (covers most of Earth)
    MIN_COORDINATE = -180               # Minimum valid coordinate value
    MAX_COORDINATE = 180                # Maximum valid coordinate value
    
    @classmethod
    def simplify_for_display(
        cls, 
        geometry: GEOSGeometry, 
        max_vertices: Optional[int] = None
    ) -> GEOSGeometry:
        """Simplify geometry for display purposes with adaptive tolerance.
        
        This function uses an adaptive approach to find the optimal simplification
        tolerance that reduces the geometry to an acceptable number of vertices
        while preserving the overall shape and topology.
        
        Args:
            geometry: Input geometry to simplify
            max_vertices: Maximum number of vertices (default: MAX_VERTICES_DISPLAY)
            
        Returns:
            Simplified geometry optimized for display
            
        Raises:
            ValueError: If geometry is invalid or unsupported
        """
        if not geometry or not geometry.valid:
            raise ValueError("Invalid geometry provided for simplification")
        
        if max_vertices is None:
            max_vertices = cls.MAX_VERTICES_DISPLAY
        
        # Count current vertices
        current_vertices = cls.count_vertices(geometry)
        
        # Return original if already within limits
        if current_vertices <= max_vertices:
            return geometry.clone()
        
        logger.debug(f"Simplifying geometry with {current_vertices} vertices to max {max_vertices}")
        
        # Use adaptive simplification
        return cls._adaptive_simplify(geometry, max_vertices)
    
    @classmethod
    def simplify_for_storage(
        cls, 
        geometry: GEOSGeometry, 
        tolerance: Optional[float] = None
    ) -> GEOSGeometry:
        """Simplify geometry for efficient storage while preserving accuracy.
        
        Args:
            geometry: Input geometry to simplify
            tolerance: Simplification tolerance (default: DEFAULT_SIMPLIFY_TOLERANCE)
            
        Returns:
            Simplified geometry optimized for storage
            
        Raises:
            ValueError: If geometry is invalid
        """
        if not geometry or not geometry.valid:
            raise ValueError("Invalid geometry provided for simplification")
        
        if tolerance is None:
            tolerance = cls.DEFAULT_SIMPLIFY_TOLERANCE
        
        # Ensure minimum tolerance
        tolerance = max(tolerance, cls.MIN_SIMPLIFY_TOLERANCE)
        
        try:
            simplified = geometry.simplify(tolerance, preserve_topology=True)
            
            # Validate result
            if not simplified.valid:
                logger.warning("Simplified geometry is invalid, using buffer(0) to fix")
                simplified = simplified.buffer(0)
            
            # Ensure proper type
            simplified = cls.normalize_geometry_type(simplified)
            
            original_vertices = cls.count_vertices(geometry)
            final_vertices = cls.count_vertices(simplified)
            
            logger.debug(
                f"Storage simplification: {original_vertices} -> {final_vertices} vertices "
                f"(tolerance: {tolerance})"
            )
            
            return simplified
            
        except GEOSException as e:
            logger.error(f"GEOS error during simplification: {e}")
            return geometry.clone()
    
    @classmethod
    def _adaptive_simplify(
        cls, 
        geometry: GEOSGeometry, 
        target_vertices: int
    ) -> GEOSGeometry:
        """Perform adaptive simplification to reach target vertex count.
        
        Args:
            geometry: Input geometry
            target_vertices: Target number of vertices
            
        Returns:
            Adaptively simplified geometry
        """
        # Start with display tolerance
        tolerance = cls.DISPLAY_SIMPLIFY_TOLERANCE
        max_iterations = 10
        iteration = 0
        
        current_geom = geometry.clone()
        
        while iteration < max_iterations:
            try:
                simplified = current_geom.simplify(tolerance, preserve_topology=True)
                
                if not simplified.valid:
                    simplified = simplified.buffer(0)
                
                vertex_count = cls.count_vertices(simplified)
                
                if vertex_count <= target_vertices:
                    # Success - we've reached the target
                    return cls.normalize_geometry_type(simplified)
                
                # Increase tolerance for next iteration
                tolerance *= 2
                iteration += 1
                
            except GEOSException as e:
                logger.warning(f"Simplification failed at tolerance {tolerance}: {e}")
                break
        
        # If adaptive simplification failed, return best effort
        logger.warning(
            f"Could not reach target vertices {target_vertices}, "
            f"returning geometry with {cls.count_vertices(current_geom)} vertices"
        )
        return current_geom
    
    @classmethod
    def normalize_geometry_type(cls, geometry: GEOSGeometry) -> MultiPolygon:
        """Normalize geometry to MultiPolygon type for consistent storage.
        
        Args:
            geometry: Input geometry (Polygon or MultiPolygon)
            
        Returns:
            MultiPolygon geometry
            
        Raises:
            ValueError: If geometry type is not supported
        """
        if geometry.geom_type == "Polygon":
            return MultiPolygon([geometry])
        elif geometry.geom_type == "MultiPolygon":
            return geometry
        else:
            raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")
    
    @classmethod
    def fix_winding_order(cls, geometry: GEOSGeometry) -> GEOSGeometry:
        """Fix winding order for polygon rings (exterior CCW, holes CW).
        
        According to OGC standards, exterior rings should be counter-clockwise
        and holes should be clockwise.
        
        Args:
            geometry: Input polygon or multipolygon geometry
            
        Returns:
            Geometry with corrected winding order
            
        Raises:
            ValueError: If geometry type is not supported
        """
        if geometry.geom_type == "Polygon":
            return cls._fix_polygon_winding(geometry)
        elif geometry.geom_type == "MultiPolygon":
            fixed_polygons = []
            for polygon in geometry:
                fixed_polygons.append(cls._fix_polygon_winding(polygon))
            return MultiPolygon(fixed_polygons)
        else:
            raise ValueError(f"Unsupported geometry type for winding order fix: {geometry.geom_type}")
    
    @classmethod
    def _fix_polygon_winding(cls, polygon: Polygon) -> Polygon:
        """Fix winding order for a single polygon.
        
        Args:
            polygon: Input polygon
            
        Returns:
            Polygon with corrected winding order
        """
        # Fix exterior ring (should be counter-clockwise)
        exterior_coords = list(polygon.exterior.coords)
        if cls._is_clockwise(exterior_coords):
            exterior_coords.reverse()
        
        # Fix holes (should be clockwise)
        fixed_holes = []
        for hole in polygon.holes:
            hole_coords = list(hole.coords)
            if not cls._is_clockwise(hole_coords):
                hole_coords.reverse()
            fixed_holes.append(LinearRing(hole_coords))
        
        return Polygon(LinearRing(exterior_coords), fixed_holes)
    
    @classmethod
    def _is_clockwise(cls, coords: List[Tuple[float, float]]) -> bool:
        """Determine if a ring of coordinates is clockwise.
        
        Uses the shoelace formula to calculate the signed area.
        Positive area = counter-clockwise, negative area = clockwise.
        
        Args:
            coords: List of coordinate tuples
            
        Returns:
            True if clockwise, False if counter-clockwise
        """
        if len(coords) < 4:  # Need at least 4 points for a closed ring
            return False
        
        # Calculate signed area using shoelace formula
        signed_area = 0.0
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            signed_area += (x2 - x1) * (y2 + y1)
        
        return signed_area > 0
    
    @classmethod
    def count_vertices(cls, geometry: GEOSGeometry) -> int:
        """Count total vertices in a geometry.
        
        Args:
            geometry: Input geometry
            
        Returns:
            Total number of vertices
        """
        if geometry.geom_type == "Polygon":
            # Count exterior ring vertices
            count = len(geometry.exterior.coords)
            # Add hole vertices
            for hole in geometry.holes:
                count += len(hole.coords)
            return count
        elif geometry.geom_type == "MultiPolygon":
            total = 0
            for polygon in geometry:
                total += cls.count_vertices(polygon)
            return total
        else:
            return 0
    
    @classmethod
    def validate_geometry(cls, geometry: GEOSGeometry) -> Tuple[bool, List[str]]:
        """Comprehensive geometry validation.
        
        This method performs extensive validation of geometry data including:
        - Basic validity (self-intersections, topology)
        - Coordinate system validation
        - Geometry type validation
        - Vertex count limits
        - Area validation
        - Coordinate bounds validation
        - Self-intersection detection
        - Hole validation
        
        Args:
            geometry: Geometry to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not geometry:
            errors.append("Geometry is None")
            return False, errors
        
        # Basic validity check
        if not geometry.valid:
            errors.append(f"Invalid geometry: {geometry.valid_reason}")
        
        # Check SRID
        if geometry.srid != 4326:
            errors.append(f"Invalid SRID: {geometry.srid}, expected 4326 (WGS84)")
        
        # Check geometry type
        if geometry.geom_type not in ["Polygon", "MultiPolygon"]:
            errors.append(f"Unsupported geometry type: {geometry.geom_type}")
        
        # Check for empty geometry
        if geometry.empty:
            errors.append("Geometry is empty")
        
        # Perform detailed validation if geometry is not empty
        if not geometry.empty:
            # Check vertex count
            vertex_count = cls.count_vertices(geometry)
            if vertex_count < cls.MIN_VERTICES_POLYGON:
                errors.append(
                    f"Too few vertices: {vertex_count}, minimum required: {cls.MIN_VERTICES_POLYGON}"
                )
            if vertex_count > cls.MAX_VERTICES_POLYGON:
                errors.append(
                    f"Too many vertices: {vertex_count}, maximum allowed: {cls.MAX_VERTICES_POLYGON}"
                )
            
            # Check area
            area = geometry.area
            if area <= 0:
                errors.append(f"Invalid area: {area}, must be greater than 0")
            elif area < cls.MIN_AREA_SQ_DEGREES:
                errors.append(
                    f"Area too small: {area}, minimum allowed: {cls.MIN_AREA_SQ_DEGREES}"
                )
            elif area > cls.MAX_AREA_SQ_DEGREES:
                errors.append(
                    f"Area too large: {area}, maximum allowed: {cls.MAX_AREA_SQ_DEGREES}"
                )
            
            # Check coordinate bounds
            bounds_errors = cls._validate_coordinate_bounds(geometry)
            errors.extend(bounds_errors)
            
            # Check for self-intersections
            if cls._has_self_intersections(geometry):
                errors.append("Geometry contains self-intersections")
            
            # Check hole validity
            hole_errors = cls._validate_holes(geometry)
            errors.extend(hole_errors)
        
        return len(errors) == 0, errors
    
    @classmethod
    def _validate_coordinate_bounds(cls, geometry: GEOSGeometry) -> List[str]:
        """Validate that all coordinates are within valid bounds.
        
        Args:
            geometry: Geometry to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Get all coordinates
            coords = []
            if geometry.geom_type == "Polygon":
                coords.extend(geometry.exterior.coords)
                for hole in geometry.holes:
                    coords.extend(hole.coords)
            elif geometry.geom_type == "MultiPolygon":
                for polygon in geometry:
                    coords.extend(polygon.exterior.coords)
                    for hole in polygon.holes:
                        coords.extend(hole.coords)
            
            # Check each coordinate
            for i, (lon, lat) in enumerate(coords):
                if not (cls.MIN_COORDINATE <= lon <= cls.MAX_COORDINATE):
                    errors.append(
                        f"Invalid longitude at vertex {i}: {lon}, "
                        f"must be between {cls.MIN_COORDINATE} and {cls.MAX_COORDINATE}"
                    )
                if not (cls.MIN_COORDINATE <= lat <= cls.MAX_COORDINATE):
                    errors.append(
                        f"Invalid latitude at vertex {i}: {lat}, "
                        f"must be between {cls.MIN_COORDINATE} and {cls.MAX_COORDINATE}"
                    )
        
        except Exception as e:
            errors.append(f"Error validating coordinate bounds: {str(e)}")
        
        return errors
    
    @classmethod
    def _has_self_intersections(cls, geometry: GEOSGeometry) -> bool:
        """Check if geometry has self-intersections.
        
        Args:
            geometry: Geometry to check
            
        Returns:
            True if geometry has self-intersections
        """
        try:
            # Use GEOS validity check which includes self-intersection detection
            return not geometry.valid
        except Exception:
            # If we can't check validity, assume it might have issues
            return True
    
    @classmethod
    def _validate_holes(cls, geometry: GEOSGeometry) -> List[str]:
        """Validate holes in polygons.
        
        Args:
            geometry: Geometry to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if geometry.geom_type == "Polygon":
                # Check that holes are inside the exterior ring
                for i, hole in enumerate(geometry.holes):
                    if not geometry.exterior.contains(hole):
                        errors.append(f"Hole {i} is not contained within exterior ring")
                    
                    # Check hole area
                    hole_area = hole.area
                    if hole_area <= 0:
                        errors.append(f"Hole {i} has invalid area: {hole_area}")
            
            elif geometry.geom_type == "MultiPolygon":
                for poly_idx, polygon in enumerate(geometry):
                    for hole_idx, hole in enumerate(polygon.holes):
                        if not polygon.exterior.contains(hole):
                            errors.append(
                                f"Hole {hole_idx} in polygon {poly_idx} is not contained within exterior ring"
                            )
                        
                        # Check hole area
                        hole_area = hole.area
                        if hole_area <= 0:
                            errors.append(
                                f"Hole {hole_idx} in polygon {poly_idx} has invalid area: {hole_area}"
                            )
        
        except Exception as e:
            errors.append(f"Error validating holes: {str(e)}")
        
        return errors
    
    @classmethod
    def repair_geometry(cls, geometry: GEOSGeometry) -> GEOSGeometry:
        """Attempt to repair invalid geometry.
        
        Args:
            geometry: Potentially invalid geometry
            
        Returns:
            Repaired geometry
        """
        if geometry.valid:
            return geometry.clone()
        
        logger.info(f"Attempting to repair invalid geometry: {geometry.valid_reason}")
        
        try:
            # Try buffer(0) approach - often fixes self-intersections
            repaired = geometry.buffer(0)
            
            if repaired.valid and not repaired.empty:
                logger.info("Successfully repaired geometry using buffer(0)")
                return cls.normalize_geometry_type(repaired)
            
            # Try more aggressive repair with small positive buffer
            repaired = geometry.buffer(0.000001)  # Very small buffer
            
            if repaired.valid and not repaired.empty:
                logger.info("Successfully repaired geometry using small buffer")
                return cls.normalize_geometry_type(repaired)
            
            logger.warning("Could not repair geometry, returning original")
            return geometry.clone()
            
        except GEOSException as e:
            logger.error(f"Error during geometry repair: {e}")
            return geometry.clone()
    
    @classmethod
    def calculate_bounds(cls, geometry: GEOSGeometry) -> Tuple[float, float, float, float]:
        """Calculate bounding box for geometry.
        
        Args:
            geometry: Input geometry
            
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        extent = geometry.extent
        return extent  # Returns (min_x, min_y, max_x, max_y)
    
    @classmethod
    def calculate_display_center(cls, geometry: GEOSGeometry) -> Point:
        """Calculate appropriate center point for display purposes.
        
        For complex geometries, this may use centroid or a more
        appropriate point that falls within the geometry.
        
        Args:
            geometry: Input geometry
            
        Returns:
            Point representing the display center
        """
        try:
            centroid = geometry.centroid
            
            # Check if centroid is within the geometry
            if geometry.contains(centroid):
                return centroid
            
            # If centroid is outside, use representative point
            return geometry.point_on_surface
            
        except GEOSException:
            # Fallback to simple centroid
            return geometry.centroid
    
    @classmethod
    def optimize_for_web(cls, geometry: GEOSGeometry) -> GEOSGeometry:
        """Optimize geometry for web display.
        
        This function applies multiple optimizations:
        - Simplification for reasonable vertex count
        - Winding order correction
        - Validation and repair
        
        Args:
            geometry: Input geometry
            
        Returns:
            Web-optimized geometry
        """
        # Start with input validation
        is_valid, errors = cls.validate_geometry(geometry)
        
        if not is_valid:
            logger.warning(f"Input geometry has validation errors: {errors}")
            geometry = cls.repair_geometry(geometry)
        
        # Simplify for display
        optimized = cls.simplify_for_display(geometry)
        
        # Fix winding order
        optimized = cls.fix_winding_order(optimized)
        
        # Final validation
        is_valid, errors = cls.validate_geometry(optimized)
        if not is_valid:
            logger.warning(f"Optimized geometry still has errors: {errors}")
        
        return optimized


# Convenience functions for direct use
def simplify_geometry(
    geometry: GEOSGeometry, 
    tolerance: float = GeometryProcessor.DEFAULT_SIMPLIFY_TOLERANCE
) -> GEOSGeometry:
    """Convenience function for geometry simplification.
    
    Args:
        geometry: Input geometry
        tolerance: Simplification tolerance
        
    Returns:
        Simplified geometry
    """
    return GeometryProcessor.simplify_for_storage(geometry, tolerance)


def normalize_multipolygon(geometry: GEOSGeometry) -> MultiPolygon:
    """Convenience function to normalize geometry to MultiPolygon.
    
    Args:
        geometry: Input geometry
        
    Returns:
        MultiPolygon geometry
    """
    return GeometryProcessor.normalize_geometry_type(geometry)


def validate_coverage_geometry(geometry: GEOSGeometry) -> Tuple[bool, List[str]]:
    """Convenience function for coverage area geometry validation.
    
    Args:
        geometry: Geometry to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return GeometryProcessor.validate_geometry(geometry)


def optimize_for_display(geometry: GEOSGeometry) -> GEOSGeometry:
    """Convenience function for display optimization.
    
    Args:
        geometry: Input geometry
        
    Returns:
        Display-optimized geometry
    """
    return GeometryProcessor.optimize_for_web(geometry)
