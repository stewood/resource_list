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
"""

from django.db import connection, models
from django.db.models import Q


class ResourceManager(models.Manager):
    """Custom manager for Resource model with advanced search and filtering capabilities.
    
    This manager provides specialized query methods for the Resource model, including:
    - Default filtering to exclude archived and deleted resources
    - Full-text search using SQLite FTS5
    - Combined search with exact matches
    - Archive-aware querying
    
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
