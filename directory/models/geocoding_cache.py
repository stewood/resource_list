"""
Geocoding Cache Model - Cache for geocoding results

This module contains the GeocodingCache model that stores geocoding results
to improve performance and reduce API calls to external geocoding services.

Author: Resource Directory Team
Created: 2025-01-15
Version: 1.0.0

Usage:
    from directory.models import GeocodingCache

    # Store a geocoding result
    cache_entry = GeocodingCache.objects.create(
        query="123 Main St, London, KY",
        latitude=37.1289,
        longitude=-84.0849,
        address="123 Main St, London, KY 40741, USA",
        provider="nominatim",
        confidence=0.8
    )

    # Look up a cached result
    cached_result = GeocodingCache.objects.filter(
        query="123 Main St, London, KY",
        expires_at__gt=timezone.now()
    ).first()
"""

import hashlib
from typing import Optional

from django.db import models
from django.utils import timezone


class GeocodingCache(models.Model):
    """Cache model for geocoding results.

    This model stores geocoding results to improve performance and reduce
    API calls to external geocoding services. It includes automatic
    expiration and confidence scoring.

    Attributes:
        query_hash: SHA-256 hash of the geocoding query for efficient lookup
        query: Original geocoding query string
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        address: Formatted address from geocoding service
        provider: Name of the geocoding provider used
        confidence: Confidence score (0.0-1.0) from the provider
        expires_at: When this cache entry expires
        created_at: When this cache entry was created
        hit_count: Number of times this cache entry has been accessed
        last_accessed: When this cache entry was last accessed
    """

    # Cache entry identification
    query_hash = models.CharField(
        max_length=64, unique=True, help_text="SHA-256 hash of the geocoding query"
    )
    query = models.TextField(help_text="Original geocoding query string")

    # Geocoding results
    latitude = models.FloatField(help_text="Latitude coordinate")
    longitude = models.FloatField(help_text="Longitude coordinate")
    address = models.TextField(help_text="Formatted address from geocoding service")

    # Metadata
    provider = models.CharField(
        max_length=50, help_text="Name of the geocoding provider used"
    )
    confidence = models.FloatField(
        null=True, blank=True, help_text="Confidence score (0.0-1.0) from the provider"
    )

    # Cache management
    expires_at = models.DateTimeField(help_text="When this cache entry expires")
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this cache entry was created"
    )
    hit_count = models.PositiveIntegerField(
        default=0, help_text="Number of times this cache entry has been accessed"
    )
    last_accessed = models.DateTimeField(
        auto_now=True, help_text="When this cache entry was last accessed"
    )

    class Meta:
        verbose_name = "Geocoding Cache Entry"
        verbose_name_plural = "Geocoding Cache Entries"
        indexes = [
            models.Index(fields=["query_hash"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["last_accessed"]),
        ]
        ordering = ["-last_accessed"]

    def __str__(self) -> str:
        return (
            f"GeocodingCache({self.query[:50]}... -> {self.latitude}, {self.longitude})"
        )

    @classmethod
    def generate_query_hash(cls, query: str) -> str:
        """Generate a SHA-256 hash for a geocoding query.

        Args:
            query: The geocoding query string

        Returns:
            str: SHA-256 hash of the query
        """
        # Normalize the query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_result(
        cls, query: str, provider: Optional[str] = None
    ) -> Optional["GeocodingCache"]:
        """Get a cached geocoding result.

        Args:
            query: The geocoding query string
            provider: Optional provider name to filter by

        Returns:
            GeocodingCache if found and not expired, None otherwise
        """
        query_hash = cls.generate_query_hash(query)

        # Build the query
        cache_query = cls.objects.filter(
            query_hash=query_hash, expires_at__gt=timezone.now()
        )

        # Filter by provider if specified
        if provider:
            cache_query = cache_query.filter(provider=provider)

        # Get the most recently accessed result
        cached_result = cache_query.order_by("-last_accessed").first()

        if cached_result:
            # Increment hit count
            cached_result.hit_count += 1
            cached_result.save(update_fields=["hit_count", "last_accessed"])

        return cached_result

    @classmethod
    def store_result(
        cls,
        query: str,
        latitude: float,
        longitude: float,
        address: str,
        provider: str,
        confidence: Optional[float] = None,
        cache_duration_hours: int = 24,
    ) -> "GeocodingCache":
        """Store a geocoding result in the cache.

        Args:
            query: The geocoding query string
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            address: Formatted address
            provider: Name of the geocoding provider
            confidence: Confidence score (0.0-1.0)
            cache_duration_hours: How long to cache the result (default: 24 hours)

        Returns:
            GeocodingCache: The created cache entry
        """
        query_hash = cls.generate_query_hash(query)
        expires_at = timezone.now() + timezone.timedelta(hours=cache_duration_hours)

        # Create or update the cache entry
        cache_entry, created = cls.objects.update_or_create(
            query_hash=query_hash,
            defaults={
                "query": query,
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "provider": provider,
                "confidence": confidence,
                "expires_at": expires_at,
                "hit_count": 1,
            },
        )

        return cache_entry

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired cache entries.

        Returns:
            int: Number of entries removed
        """
        expired_count, _ = cls.objects.filter(expires_at__lte=timezone.now()).delete()

        return expired_count

    @classmethod
    def cleanup_old_entries(cls, days_old: int = 7) -> int:
        """Remove old cache entries regardless of expiration.

        Args:
            days_old: Remove entries older than this many days

        Returns:
            int: Number of entries removed
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)

        old_count, _ = cls.objects.filter(created_at__lte=cutoff_date).delete()

        return old_count

    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics.

        Returns:
            dict: Cache statistics including total entries, expired entries, etc.
        """
        total_entries = cls.objects.count()
        expired_entries = cls.objects.filter(expires_at__lte=timezone.now()).count()
        active_entries = total_entries - expired_entries

        # Get provider distribution
        provider_stats = (
            cls.objects.values("provider")
            .annotate(count=models.Count("id"))
            .order_by("-count")
        )

        # Get average hit count
        avg_hit_count = (
            cls.objects.aggregate(avg_hits=models.Avg("hit_count"))["avg_hits"] or 0
        )

        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "provider_distribution": list(provider_stats),
            "average_hit_count": round(avg_hit_count, 2),
        }
