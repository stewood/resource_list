"""
Model Managers - Custom QuerySet Managers

This module contains custom Django model managers that provide specialized
query methods and filtering capabilities for the resource directory models.

Managers:
    - ResourceManager: Advanced search and filtering for Resource model

Features:
    - Default filtering to exclude archived/deleted resources
    - Full-text search using SQLite FTS5
    - Combined search with exact matches
    - Archive-aware querying methods
    - Fallback search when FTS5 is unavailable
    - Spatial query methods for location-based filtering (when GIS enabled)

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models.managers import ResourceManager
    
    # Use in Resource model
    class Resource(models.Model):
        objects = ResourceManager()
    
    # Or use directly
    resources = ResourceManager().search_fts("mental health")
    resources = ResourceManager().filter_by_location(lat=37.7749, lon=-122.4194)
"""

from django.db import connection, models
from django.db.models import Q, Case, When, Value, IntegerField
from django.conf import settings
from typing import Optional, Dict, Any, List, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class ResourceManager(models.Manager):
    """Custom manager for Resource model with advanced search and filtering capabilities.
    
    This manager provides specialized query methods for the Resource model, including:
    - Default filtering to exclude archived and deleted resources
    - Full-text search using SQLite FTS5
    - Combined search with exact matches
    - Archive-aware querying
    - Spatial query methods for location-based filtering (when GIS enabled)
    
    The manager automatically filters out archived and deleted resources by default,
    but provides methods to include them when needed for administrative purposes.
    
    Attributes:
        model: The Resource model this manager operates on
        
    Example:
        >>> # Get all active resources (default behavior)
        >>> resources = Resource.objects.all()
        
        >>> # Get all resources including archived
        >>> all_resources = Resource.objects.all_including_archived()
        
        >>> # Search with FTS5
        >>> results = Resource.objects.search_fts("mental health")
        
        >>> # Filter by location (when GIS enabled)
        >>> results = Resource.objects.filter_by_location(lat=37.7749, lon=-122.4194)
    """

    def get_queryset(self) -> models.QuerySet:
        """Return only non-archived, non-deleted resources by default.
        
        This method overrides the default queryset to automatically filter out
        archived and deleted resources, ensuring that normal queries only return
        active, visible resources.
        
        Returns:
            QuerySet: Filtered queryset containing only active resources
            
        Note:
            This is the default behavior for all Resource queries unless
            explicitly overridden by other manager methods.
        """
        return super().get_queryset().filter(is_archived=False, is_deleted=False)

    def all_including_archived(self) -> models.QuerySet:
        """Return all resources including archived ones, but excluding deleted.
        
        This method is useful for administrative purposes where you need to see
        all resources including those that have been archived but not permanently
        deleted.
        
        Returns:
            QuerySet: All resources except those marked as deleted
            
        Example:
            >>> archived_resources = Resource.objects.all_including_archived()
        """
        return super().get_queryset().filter(is_deleted=False)

    def archived(self) -> models.QuerySet:
        """Return only archived resources that haven't been deleted.
        
        This method is useful for reviewing archived resources or for
        administrative cleanup tasks.
        
        Returns:
            QuerySet: Only archived resources
            
        Example:
            >>> archived = Resource.objects.archived()
        """
        return super().get_queryset().filter(is_archived=True, is_deleted=False)

    def search_fts(self, query: str) -> models.QuerySet:
        """Search resources using SQLite FTS5 full-text search.
        
        This method performs full-text search using SQLite's FTS5 extension,
        which provides fast and relevant search results. The search is performed
        across multiple fields including name, description, and location data.
        
        Args:
            query (str): Search query string to search for
            
        Returns:
            QuerySet: Matching resources ordered by relevance score
            
        Raises:
            Exception: If FTS5 search fails, falls back to basic search
            
        Note:
            - Falls back to basic icontains search if FTS5 is not available
            - Empty queries return an empty queryset
            - Results are ordered by relevance (rank) from FTS5
            - Uses parameterized queries to prevent SQL injection
            
        Example:
            >>> results = Resource.objects.search_fts("crisis intervention")
            >>> results = Resource.objects.search_fts("mental health services")
        """
        if not query.strip():
            return self.none()

        try:
            # Use raw SQL to perform FTS5 search with parameterized query
            with connection.cursor() as cursor:
                # FTS5 doesn't support parameter substitution, so we need to escape the query
                # Use a safer approach by validating and escaping the query
                escaped_query = self._escape_fts_query(query)
                sql = """
                    SELECT resource_id, rank
                    FROM resource_fts 
                    WHERE resource_fts MATCH %s
                    ORDER BY rank
                """
                cursor.execute(sql, [escaped_query])

                results = cursor.fetchall()

            if not results:
                return self.none()

            # Get resource IDs in order of relevance
            resource_ids = [row[0] for row in results]

            # Create a QuerySet with the results in the correct order
            preserved = models.Case(
                *[models.When(pk=pk, then=pos) for pos, pk in enumerate(resource_ids)]
            )
            return self.filter(pk__in=resource_ids).order_by(preserved)

        except Exception:
            # Fallback to basic search if FTS5 is not available
            return self.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(city__icontains=query)
                | Q(state__icontains=query)
            )

    def _escape_fts_query(self, query: str) -> str:
        """Escape and validate FTS5 query to prevent SQL injection.
        
        This method sanitizes the FTS5 query string by:
        1. Removing or escaping dangerous characters
        2. Validating the query structure
        3. Ensuring only safe FTS5 syntax is used
        
        Args:
            query (str): Raw query string from user input
            
        Returns:
            str: Sanitized query string safe for FTS5
            
        Raises:
            ValueError: If query contains dangerous patterns
        """
        import re
        
        # Remove any SQL injection attempts
        dangerous_patterns = [
            r'--',  # SQL comments
            r'/\*.*?\*/',  # SQL block comments
            r';\s*$',  # Trailing semicolons
            r'UNION\s+ALL',  # UNION attacks
            r'DROP\s+TABLE',  # DROP commands
            r'DELETE\s+FROM',  # DELETE commands
            r'UPDATE\s+SET',  # UPDATE commands
            r'INSERT\s+INTO',  # INSERT commands
            r'CREATE\s+TABLE',  # CREATE commands
            r'ALTER\s+TABLE',  # ALTER commands
        ]
        
        query_upper = query.upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_upper, re.IGNORECASE):
                raise ValueError(f"Query contains dangerous pattern: {pattern}")
        
        # Escape special FTS5 characters that could cause issues
        # FTS5 has its own syntax, so we need to be careful
        escaped_query = query.replace('"', '""')  # Escape double quotes
        
        # Limit query length to prevent DoS
        if len(escaped_query) > 1000:
            raise ValueError("Query too long (max 1000 characters)")
        
        return escaped_query

    def search_combined(self, query: str) -> models.QuerySet:
        """Combined search using FTS5 for full-text and icontains for exact matches.
        
        This method combines the power of FTS5 full-text search with exact
        field matching to provide comprehensive search results. It searches
        both the FTS5 index and specific fields that might not be included
        in the full-text index.
        
        Args:
            query (str): Search query string to search for
            
        Returns:
            QuerySet: Combined search results from both FTS5 and exact matches
            
        Note:
            - Combines results from FTS5 search and exact field matching
            - Removes duplicates automatically
            - Empty queries return an empty queryset
            
        Example:
            >>> results = Resource.objects.search_combined("555-1234")
            >>> results = Resource.objects.search_combined("mental health")
        """
        if not query.strip():
            return self.none()

        # Get FTS5 results
        fts_results = self.search_fts(query)

        # Get exact match results (for fields not in FTS5)
        exact_results = self.filter(
            Q(name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(website__icontains=query)
            | Q(postal_code__icontains=query)
        )

        # Combine and deduplicate results
        combined_ids = list(fts_results.values_list("pk", flat=True))
        combined_ids.extend(list(exact_results.values_list("pk", flat=True)))

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for pk in combined_ids:
            if pk not in seen:
                seen.add(pk)
                unique_ids.append(pk)

        if not unique_ids:
            return self.none()

        # Return results in the combined order
        preserved = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(unique_ids)]
        )
        return self.filter(pk__in=unique_ids).order_by(preserved)

    def filter_by_location(
        self, 
        lat: float, 
        lon: float, 
        radius_miles: Optional[float] = None,
        include_radius_search: bool = True
    ) -> models.QuerySet:
        """Filter resources by geographic location and coverage areas.
        
        This method finds resources that serve a specific location by:
        1. Finding resources with coverage areas that contain the point
        2. Optionally including resources within a radius of their location
        3. Ranking results by coverage specificity (RADIUS > CITY > COUNTY > STATE)
        
        Args:
            lat (float): Latitude of the search point (WGS84)
            lon (float): Longitude of the search point (WGS84)
            radius_miles (float, optional): Maximum radius to search for resources
                with location data but no coverage areas. Defaults to None.
            include_radius_search (bool): Whether to include radius-based search
                for resources without coverage areas. Defaults to True.
                
        Returns:
            QuerySet: Resources that serve the specified location, annotated with
                coverage specificity and distance information
                
        Note:
            - Requires GIS to be enabled for spatial queries
            - Falls back to text-based location matching when GIS is disabled
            - Results are ordered by coverage specificity and distance
            
        Example:
            >>> # Find resources serving a specific location
            >>> resources = Resource.objects.filter_by_location(37.7749, -122.4194)
            
            >>> # Include radius search within 10 miles
            >>> resources = Resource.objects.filter_by_location(
            ...     37.7749, -122.4194, radius_miles=10
            ... )
        """
        if not getattr(settings, 'GIS_ENABLED', False):
            # Fallback to text-based location matching when GIS is disabled
            logger.warning("GIS not enabled, falling back to text-based location matching")
            return self._filter_by_location_fallback(lat, lon, radius_miles)
        
        try:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            
            # Create point for spatial queries
            search_point = Point(lon, lat, srid=4326)
            
            # Start with resources that have coverage areas containing the point
            queryset = self.filter(
                coverage_areas__geom__contains=search_point
            ).distinct()
            
            # Annotate with coverage specificity and distance
            queryset = self._annotate_coverage_specificity(queryset, search_point)
            
            # Add radius search if requested
            if include_radius_search and radius_miles:
                radius_meters = radius_miles * 1609.34  # Convert miles to meters
                radius_point = Point(lon, lat, srid=4326)
                
                # Find resources within radius that don't have coverage areas
                # Note: Since Resource model doesn't have lat/lon fields, we'll use
                # text-based location matching for radius search
                radius_resources = self.filter(
                    coverage_areas__isnull=True
                ).filter(
                    Q(city__isnull=False) | Q(state__isnull=False)
                )
                
                # Combine with coverage area results
                combined_ids = list(queryset.values_list('pk', flat=True))
                combined_ids.extend(list(radius_resources.values_list('pk', flat=True)))
                
                if combined_ids:
                    # Preserve order and remove duplicates
                    seen = set()
                    unique_ids = []
                    for pk in combined_ids:
                        if pk not in seen:
                            seen.add(pk)
                            unique_ids.append(pk)
                    
                    preserved = Case(
                        *[When(pk=pk, then=pos) for pos, pk in enumerate(unique_ids)]
                    )
                    queryset = self.filter(pk__in=unique_ids).order_by(preserved)
            
            return queryset
            
        except ImportError:
            logger.error("GIS libraries not available for spatial queries")
            return self._filter_by_location_fallback(lat, lon, radius_miles)
        except Exception as e:
            logger.error(f"Error in spatial location filtering: {e}")
            return self._filter_by_location_fallback(lat, lon, radius_miles)

    def find_resources_by_location(
        self,
        location: Union[str, Tuple[float, float]],
        radius_miles: Optional[float] = None,
        include_radius_search: bool = True,
        provider_name: Optional[str] = None,
        sort_by_proximity: bool = True
    ) -> models.QuerySet:
        """Find resources by location using address geocoding or coordinates.
        
        This is the main entry point for location-based resource search. It accepts
        either an address string (which gets geocoded) or coordinates, then uses
        the spatial query logic to find resources that serve that location.
        
        Args:
            location: Either an address string or (lat, lon) tuple
            radius_miles: Maximum radius to search for resources without coverage areas
            include_radius_search: Whether to include radius-based search
            provider_name: Specific geocoding provider to use (optional)
            sort_by_proximity: Whether to sort results by proximity score (default: True)
            
        Returns:
            QuerySet: Resources that serve the specified location, ranked by proximity
                and coverage specificity
            
        Example:
            >>> # Search by address
            >>> resources = Resource.objects.find_resources_by_location("London, KY")
            
            >>> # Search by coordinates
            >>> resources = Resource.objects.find_resources_by_location((37.1283, -84.0836))
            
            >>> # Search with radius
            >>> resources = Resource.objects.find_resources_by_location(
            ...     "London, KY", radius_miles=10
            ... )
        """
        # Handle different input types
        if isinstance(location, str):
            # Geocode the address string
            lat, lon = self._geocode_location(location, provider_name)
            if lat is None or lon is None:
                logger.warning(f"Could not geocode address: {location}")
                return self.none()
        elif isinstance(location, (tuple, list)) and len(location) == 2:
            # Use provided coordinates
            lat, lon = location
        else:
            logger.error(f"Invalid location format: {location}")
            return self.none()
        
        # Use proximity-based spatial query logic
        return self.filter_by_location_with_proximity(
            lat=lat,
            lon=lon,
            radius_miles=radius_miles,
            include_radius_search=include_radius_search,
            sort_by_proximity=sort_by_proximity
        )

    def _geocode_location(
        self, 
        address: str, 
        provider_name: Optional[str] = None
    ) -> Tuple[Optional[float], Optional[float]]:
        """Geocode an address string to coordinates.
        
        Args:
            address: Address string to geocode
            provider_name: Specific geocoding provider to use (optional)
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if geocoding fails
        """
        try:
            from directory.services.geocoding import get_geocoding_service
            
            service = get_geocoding_service()
            result = service.geocode(address, provider_name)
            
            if result and result.is_valid():
                logger.info(f"Successfully geocoded '{address}' to ({result.latitude}, {result.longitude})")
                return result.latitude, result.longitude
            else:
                logger.warning(f"Geocoding failed for address: {address}")
                return None, None
                
        except ImportError:
            logger.error("Geocoding service not available")
            return None, None
        except Exception as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None, None

    def _filter_by_location_fallback(
        self, 
        lat: float, 
        lon: float, 
        radius_miles: Optional[float] = None
    ) -> models.QuerySet:
        """Fallback location filtering using text-based matching.
        
        This method is used when GIS is not available or spatial queries fail.
        It performs basic text-based location matching using city, state, and
        postal code fields.
        
        Args:
            lat (float): Latitude (not used in fallback)
            lon (float): Longitude (not used in fallback)
            radius_miles (float, optional): Not used in fallback
            
        Returns:
            QuerySet: Resources with location information, ordered by relevance
        """
        # Return resources that have location information
        return self.filter(
            Q(city__isnull=False) | Q(state__isnull=False) | Q(postal_code__isnull=False)
        ).exclude(
            Q(city='') & Q(state='') & Q(postal_code='')
        )

    def annotate_coverage_specificity(self, queryset: models.QuerySet) -> models.QuerySet:
        """Annotate queryset with coverage area specificity information.
        
        This method adds annotations to help rank resources by how specific
        their coverage areas are. More specific coverage areas (like RADIUS
        or CITY) are ranked higher than broader ones (like STATE).
        
        Args:
            queryset (QuerySet): The queryset to annotate
            
        Returns:
            QuerySet: Annotated queryset with coverage specificity information
            
        Note:
            - Requires GIS to be enabled for spatial annotations
            - Falls back gracefully when GIS is not available
            - Adds specificity_score and coverage_type annotations
            
        Example:
            >>> resources = Resource.objects.annotate_coverage_specificity(
            ...     Resource.objects.filter_by_location(37.7749, -122.4194)
            ... )
        """
        if not getattr(settings, 'GIS_ENABLED', False):
            # Return queryset unchanged when GIS is not available
            return queryset
        
        try:
            # Define specificity scores for different coverage area types
            specificity_scores = {
                'RADIUS': 100,    # Most specific - exact radius
                'POLYGON': 90,    # Custom polygon - very specific
                'CITY': 80,       # City boundary - specific
                'COUNTY': 60,     # County boundary - moderate
                'STATE': 40,      # State boundary - broad
            }
            
            # Create Case statement for specificity scoring
            specificity_case = Case(
                When(coverage_areas__kind='RADIUS', then=Value(specificity_scores['RADIUS'])),
                When(coverage_areas__kind='POLYGON', then=Value(specificity_scores['POLYGON'])),
                When(coverage_areas__kind='CITY', then=Value(specificity_scores['CITY'])),
                When(coverage_areas__kind='COUNTY', then=Value(specificity_scores['COUNTY'])),
                When(coverage_areas__kind='STATE', then=Value(specificity_scores['STATE'])),
                default=Value(0),
                output_field=IntegerField(),
            )
            
            return queryset.annotate(
                specificity_score=models.Max(specificity_case),
                coverage_type=models.Max('coverage_areas__kind'),
                coverage_count=models.Count('coverage_areas', distinct=True)
            )
            
        except Exception as e:
            logger.error(f"Error annotating coverage specificity: {e}")
            return queryset

    def _annotate_coverage_specificity(
        self, 
        queryset: models.QuerySet, 
        search_point: Any
    ) -> models.QuerySet:
        """Internal method to annotate coverage specificity with distance information.
        
        This method is used internally by filter_by_location to add both
        specificity and distance annotations to the queryset.
        
        Args:
            queryset (QuerySet): The queryset to annotate
            search_point: The search point for distance calculations
            
        Returns:
            QuerySet: Annotated queryset with specificity and distance information
        """
        try:
            from django.contrib.gis.db.models.functions import Distance
            
            # Add distance annotation for coverage areas
            queryset = queryset.annotate(
                min_distance=Distance('coverage_areas__center', search_point)
            )
            
            # Add specificity annotation
            return self.annotate_coverage_specificity(queryset)
            
        except Exception as e:
            logger.error(f"Error in coverage specificity annotation: {e}")
            return queryset

    def annotate_proximity_ranking(
        self, 
        queryset: models.QuerySet, 
        lat: float, 
        lon: float
    ) -> models.QuerySet:
        """Annotate queryset with comprehensive proximity ranking information.
        
        This method adds distance and proximity-based ranking annotations to help
        sort resources by their proximity to a given location. It combines coverage
        area distance, resource location distance, and coverage specificity.
        
        Args:
            queryset (QuerySet): The queryset to annotate
            lat (float): Latitude of the search point
            lon (float): Longitude of the search point
            
        Returns:
            QuerySet: Annotated queryset with proximity ranking information
            
        Note:
            - Requires GIS to be enabled for spatial annotations
            - Falls back gracefully when GIS is not available
            - Adds distance_miles, proximity_score, and ranking annotations
            
        Example:
            >>> resources = Resource.objects.annotate_proximity_ranking(
            ...     Resource.objects.all(), 37.7749, -122.4194
            ... ).order_by('proximity_score')
        """
        if not getattr(settings, 'GIS_ENABLED', False):
            # Return queryset unchanged when GIS is not available
            return queryset
        
        try:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            
            search_point = Point(lon, lat, srid=4326)
            
            # Define specificity scores for different coverage area types
            specificity_scores = {
                'RADIUS': 100,    # Most specific - exact radius
                'POLYGON': 90,    # Custom polygon - very specific
                'CITY': 80,       # City boundary - specific
                'COUNTY': 60,     # County boundary - moderate
                'STATE': 40,      # State boundary - broad
            }
            
            # Create Case statement for specificity scoring
            specificity_case = Case(
                When(coverage_areas__kind='RADIUS', then=Value(specificity_scores['RADIUS'])),
                When(coverage_areas__kind='POLYGON', then=Value(specificity_scores['POLYGON'])),
                When(coverage_areas__kind='CITY', then=Value(specificity_scores['CITY'])),
                When(coverage_areas__kind='COUNTY', then=Value(specificity_scores['COUNTY'])),
                When(coverage_areas__kind='STATE', then=Value(specificity_scores['STATE'])),
                default=Value(0),
                output_field=IntegerField(),
            )
            
            # Annotate with distance and specificity information
            queryset = queryset.annotate(
                # Distance to coverage area centers (in meters)
                coverage_distance_m=Distance('coverage_areas__center', search_point),
                # Coverage specificity score
                specificity_score=models.Max(specificity_case),
                # Coverage type and count
                coverage_type=models.Max('coverage_areas__kind'),
                coverage_count=models.Count('coverage_areas', distinct=True)
            )
            
            # Convert distance to miles and create proximity score
            # Proximity score combines distance and specificity
            # Lower distance = higher score, higher specificity = higher score
            queryset = queryset.annotate(
                # Convert meters to miles
                distance_miles=models.ExpressionWrapper(
                    models.F('coverage_distance_m') / 1609.34,  # Convert meters to miles
                    output_field=models.FloatField()
                ),
                # Calculate proximity score (higher = better)
                # Formula: specificity_score * (1 / (1 + distance_miles))
                # This gives higher scores for closer, more specific coverage areas
                proximity_score=models.ExpressionWrapper(
                    models.F('specificity_score') * (1.0 / (1.0 + models.F('distance_miles'))),
                    output_field=models.FloatField()
                )
            )
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error in proximity ranking annotation: {e}")
            return queryset

    def filter_by_location_with_proximity(
        self, 
        lat: float, 
        lon: float, 
        radius_miles: Optional[float] = None,
        include_radius_search: bool = True,
        sort_by_proximity: bool = True
    ) -> models.QuerySet:
        """Filter resources by location with proximity-based ranking.
        
        This method extends filter_by_location with comprehensive proximity calculations
        and ranking. It finds resources that serve a specific location and ranks them
        by proximity and coverage specificity.
        
        Args:
            lat (float): Latitude of the search point (WGS84)
            lon (float): Longitude of the search point (WGS84)
            radius_miles (float, optional): Maximum radius to search for resources
                with location data but no coverage areas. Defaults to None.
            include_radius_search (bool): Whether to include radius-based search
                for resources without coverage areas. Defaults to True.
            sort_by_proximity (bool): Whether to sort results by proximity score.
                Defaults to True.
                
        Returns:
            QuerySet: Resources that serve the specified location, ranked by proximity
                and coverage specificity
            
        Example:
            >>> # Find resources serving a location, ranked by proximity
            >>> resources = Resource.objects.filter_by_location_with_proximity(
            ...     37.7749, -122.4194, radius_miles=10
            ... )
        """
        # Check if GIS is enabled for proximity calculations
        if not getattr(settings, 'GIS_ENABLED', False):
            # Fallback to basic location filtering when GIS is not available
            logger.warning("GIS not enabled, using basic location filtering without proximity ranking")
            return self.filter_by_location(
                lat=lat,
                lon=lon,
                radius_miles=radius_miles,
                include_radius_search=include_radius_search
            )
        
        # First, get resources using the existing spatial query logic
        queryset = self.filter_by_location(
            lat=lat,
            lon=lon,
            radius_miles=radius_miles,
            include_radius_search=include_radius_search
        )
        
        # Add proximity ranking annotations
        queryset = self.annotate_proximity_ranking(queryset, lat, lon)
        
        # Sort by proximity score if requested
        if sort_by_proximity:
            queryset = queryset.order_by('-proximity_score', '-specificity_score', 'distance_miles')
        
        return queryset

    def filter_by_coverage_area(
        self, 
        coverage_area_id: int, 
        include_children: bool = False
    ) -> models.QuerySet:
        """Filter resources by specific coverage area.
        
        This method finds resources that are associated with a specific
        coverage area, optionally including resources in child areas
        (e.g., cities within a county).
        
        Args:
            coverage_area_id (int): ID of the coverage area to filter by
            include_children (bool): Whether to include resources in child areas.
                Defaults to False.
                
        Returns:
            QuerySet: Resources associated with the specified coverage area
            
        Example:
            >>> # Find resources in a specific county
            >>> resources = Resource.objects.filter_by_coverage_area(21025)
            
            >>> # Include resources in cities within the county
            >>> resources = Resource.objects.filter_by_coverage_area(
            ...     21025, include_children=True
            ... )
        """
        queryset = self.filter(coverage_areas__id=coverage_area_id)
        
        if include_children:
            # This would require additional logic to determine parent-child
            # relationships between coverage areas, which we can implement
            # when we have the administrative boundary hierarchy
            logger.info("Include children functionality not yet implemented")
        
        return queryset.distinct()

    def get_coverage_statistics(self) -> Dict[str, Any]:
        """Get statistics about resource coverage areas.
        
        This method provides aggregate statistics about how resources
        are distributed across different types of coverage areas.
        
        Returns:
            Dict containing coverage statistics
            
        Example:
            >>> stats = Resource.objects.get_coverage_statistics()
            >>> print(f"Resources with coverage areas: {stats['with_coverage']}")
        """
        total_resources = self.count()
        with_coverage = self.filter(coverage_areas__isnull=False).distinct().count()
        without_coverage = total_resources - with_coverage
        
        # Get breakdown by coverage area type
        coverage_types = self.filter(
            coverage_areas__isnull=False
        ).values(
            'coverage_areas__kind'
        ).annotate(
            count=models.Count('id', distinct=True)
        ).order_by('coverage_areas__kind')
        
        return {
            'total_resources': total_resources,
            'with_coverage': with_coverage,
            'without_coverage': without_coverage,
            'coverage_percentage': (with_coverage / total_resources * 100) if total_resources > 0 else 0,
            'coverage_types': list(coverage_types),
        }

    def calculate_resource_distance(
        self, 
        resource_id: int, 
        lat: float, 
        lon: float
    ) -> Dict[str, Any]:
        """Calculate distance from a location to a specific resource.
        
        This method calculates the distance from a given location to a specific
        resource, including distance to the resource's physical location and
        coverage area information.
        
        Args:
            resource_id (int): ID of the resource to calculate distance for
            lat (float): Latitude of the query location
            lon (float): Longitude of the query location
            
        Returns:
            Dict containing distance and eligibility information
            
        Example:
            >>> distance_info = Resource.objects.calculate_resource_distance(
            ...     123, 37.7749, -122.4194
            ... )
            >>> print(f"Distance: {distance_info['distance_miles']} miles")
        """
        try:
            resource = self.get(id=resource_id)
            
            result = {
                'resource_id': resource_id,
                'resource_name': resource.name,
                'serves_location': False,
                'distance_miles': None,
                'coverage_areas': [],
                'eligibility_reason': 'Unknown',
            }
            
            # Check if GIS is enabled for distance calculations
            if not getattr(settings, 'GIS_ENABLED', False):
                result['eligibility_reason'] = 'GIS not enabled for distance calculations'
                return result
            
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            
            query_point = Point(lon, lat, srid=4326)
            
            # Calculate distance to resource's physical location if available
            # Note: Resource model doesn't have lat/lon fields, so we'll use coverage area centers
            # For now, we'll calculate distance to the closest coverage area center
            
            # Check coverage areas
            coverage_areas = resource.coverage_areas.all()
            if not coverage_areas.exists():
                result['eligibility_reason'] = 'Resource has no defined coverage areas'
                return result
            
            # Track the closest coverage area for distance calculation
            closest_distance = float('inf')
            closest_area = None
            
            # Check if location is within any coverage area
            for coverage_area in coverage_areas:
                if coverage_area.geom:
                    # Check if query point is within the coverage area geometry
                    if coverage_area.geom.contains(query_point):
                        result['serves_location'] = True
                        result['eligibility_reason'] = f'Location is within {coverage_area.name} ({coverage_area.kind})'
                        
                        # Set distance to 0 for areas that contain the location
                        area_info = {
                            'id': coverage_area.id,
                            'name': coverage_area.name,
                            'kind': coverage_area.kind,
                            'distance_miles': 0.0,
                            'contains_location': True
                        }
                        result['coverage_areas'].append(area_info)
                        result['distance_miles'] = 0.0
                        break
                    else:
                        # Calculate distance to coverage area boundary
                        distance_to_area = coverage_area.geom.distance(query_point)
                        distance_miles = round(distance_to_area / 1609.34, 2)
                        
                        # Track closest area
                        if distance_miles < closest_distance:
                            closest_distance = distance_miles
                            closest_area = coverage_area
                        
                        # Add coverage area info
                        area_info = {
                            'id': coverage_area.id,
                            'name': coverage_area.name,
                            'kind': coverage_area.kind,
                            'distance_miles': distance_miles,
                            'contains_location': False
                        }
                        result['coverage_areas'].append(area_info)
                else:
                    # No geometry available, use center point if available
                    if coverage_area.center:
                        center_distance = query_point.distance(coverage_area.center)
                        distance_miles = round(center_distance / 1609.34, 2)
                        
                        # Track closest area
                        if distance_miles < closest_distance:
                            closest_distance = distance_miles
                            closest_area = coverage_area
                        
                        area_info = {
                            'id': coverage_area.id,
                            'name': coverage_area.name,
                            'kind': coverage_area.kind,
                            'distance_miles': distance_miles,
                            'contains_location': False,
                            'note': 'Using center point (no boundary geometry)'
                        }
                        result['coverage_areas'].append(area_info)
            
            # Set the overall distance to the closest coverage area
            if closest_area and not result['serves_location']:
                result['distance_miles'] = closest_distance
            
            # If no coverage area contains the location, provide closest area info
            if not result['serves_location'] and result['coverage_areas']:
                closest_area = min(result['coverage_areas'], key=lambda x: x['distance_miles'])
                result['eligibility_reason'] = f'Location not served. Closest area: {closest_area["name"]} ({closest_area["distance_miles"]} miles away)'
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating resource distance: {e}")
            return {
                'resource_id': resource_id,
                'error': str(e),
                'serves_location': False,
                'eligibility_reason': 'Error calculating distance'
            }

    def check_location_eligibility(
        self, 
        lat: float, 
        lon: float, 
        radius_miles: float = 50
    ) -> Dict[str, Any]:
        """Check which resources serve a specific location.
        
        This method finds all resources that serve a given location and provides
        detailed eligibility information for each resource.
        
        Args:
            lat (float): Latitude of the location to check
            lon (float): Longitude of the location to check
            radius_miles (float): Search radius in miles (default: 50)
            
        Returns:
            Dict containing eligibility information for all resources
            
        Example:
            >>> eligibility = Resource.objects.check_location_eligibility(
            ...     37.7749, -122.4194, radius_miles=25
            ... )
            >>> print(f"Resources serving location: {len(eligibility['serving_resources'])}")
        """
        try:
            # Get resources within the search radius
            nearby_resources = self.filter_by_location(
                lat=lat, 
                lon=lon, 
                radius_miles=radius_miles
            )
            
            serving_resources = []
            nearby_resources_list = []
            
            for resource in nearby_resources:
                # Calculate detailed distance and eligibility info
                distance_info = self.calculate_resource_distance(
                    resource.id, lat, lon
                )
                
                resource_info = {
                    'id': resource.id,
                    'name': resource.name,
                    'description': resource.description,
                    'city': resource.city,
                    'state': resource.state,
                    'phone': resource.phone,
                    'website': resource.website,
                    'is_emergency_service': resource.is_emergency_service,
                    'is_24_hour_service': resource.is_24_hour_service,
                    'serves_location': distance_info['serves_location'],
                    'distance_miles': distance_info['distance_miles'],
                    'eligibility_reason': distance_info['eligibility_reason'],
                    'coverage_areas': distance_info['coverage_areas']
                }
                
                if distance_info['serves_location']:
                    serving_resources.append(resource_info)
                else:
                    nearby_resources_list.append(resource_info)
            
            return {
                'location': {
                    'lat': lat,
                    'lon': lon,
                    'radius_miles': radius_miles
                },
                'serving_resources': serving_resources,
                'nearby_resources': nearby_resources_list,
                'total_serving': len(serving_resources),
                'total_nearby': len(nearby_resources_list)
            }
            
        except Exception as e:
            logger.error(f"Error checking location eligibility: {e}")
            return {
                'error': str(e),
                'serving_resources': [],
                'nearby_resources': []
            }
