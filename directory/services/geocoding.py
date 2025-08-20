"""Geocoding service abstraction layer.

This module provides an abstraction layer for geocoding services, allowing
easy switching between different providers (Nominatim, Google, etc.) and
implementing caching and error handling.

Classes:
    GeocodingResult: Result object for geocoding operations
    GeocodingProvider: Abstract base class for geocoding providers
    NominatimProvider: Implementation using OpenStreetMap Nominatim
    GeocodingService: Main service class with provider management

Example:
    >>> from directory.services.geocoding import GeocodingService
    >>> service = GeocodingService()
    >>> result = service.geocode("123 Main St, London, KY")
    >>> print(f"Lat: {result.latitude}, Lon: {result.longitude}")
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote

import requests
from django.conf import settings
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


class GeocodingResult:
    """Result object for geocoding operations.
    
    Attributes:
        latitude: Latitude coordinate (float)
        longitude: Longitude coordinate (float)
        address: Formatted address string
        raw_data: Raw response data from provider
        provider: Name of the provider used
        confidence: Confidence score (0.0-1.0) if available
        cache_hit: Whether this result came from cache
    """
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        address: str,
        raw_data: Dict = None,
        provider: str = "unknown",
        confidence: Optional[float] = None,
        cache_hit: bool = False,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.raw_data = raw_data or {}
        self.provider = provider
        self.confidence = confidence
        self.cache_hit = cache_hit
    
    def __str__(self) -> str:
        return f"GeocodingResult({self.latitude}, {self.longitude}, '{self.address}')"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        """Return coordinates as a tuple (lat, lon)."""
        return (self.latitude, self.longitude)
    
    def is_valid(self) -> bool:
        """Check if the result has valid coordinates."""
        return (
            -90 <= self.latitude <= 90 and
            -180 <= self.longitude <= 180 and
            self.latitude != 0 or self.longitude != 0
        )


class GeocodingProvider(ABC):
    """Abstract base class for geocoding providers.
    
    This class defines the interface that all geocoding providers must implement.
    Providers handle the actual communication with external geocoding services.
    """
    
    def __init__(self, name: str, rate_limit_per_minute: int = 60):
        """Initialize the provider.
        
        Args:
            name: Provider name for identification
            rate_limit_per_minute: Rate limit for API calls
        """
        self.name = name
        self.rate_limit_per_minute = rate_limit_per_minute
        self.last_request_time = 0
    
    @abstractmethod
    def geocode(self, query: str) -> Optional[GeocodingResult]:
        """Geocode an address or location query.
        
        Args:
            query: Address or location string to geocode
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        pass
    
    @abstractmethod
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodingResult]:
        """Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        pass
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.rate_limit_per_minute
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class NominatimProvider(GeocodingProvider):
    """Nominatim geocoding provider using OpenStreetMap data.
    
    This provider uses the Nominatim service for geocoding. It's free to use
    but has rate limits and should be used with respect for the service.
    
    Attributes:
        base_url: Nominatim API base URL
        user_agent: User agent string for API requests
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "ResourceDirectory/1.0",
        timeout: int = 10,
        rate_limit_per_minute: int = 60,
    ):
        """Initialize Nominatim provider.
        
        Args:
            base_url: Nominatim API base URL
            user_agent: User agent string for API requests
            timeout: Request timeout in seconds
            rate_limit_per_minute: Rate limit (default 60/min for Nominatim)
        """
        super().__init__("nominatim", rate_limit_per_minute)
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout
        self._geocoder = None
    
    @property
    def geocoder(self) -> Nominatim:
        """Get or create the Nominatim geocoder instance."""
        if self._geocoder is None:
            self._geocoder = Nominatim(
                user_agent=self.user_agent,
                timeout=self.timeout
            )
        return self._geocoder
    
    def geocode(self, query: str) -> Optional[GeocodingResult]:
        """Geocode an address using Nominatim.
        
        Args:
            query: Address string to geocode
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        try:
            self._rate_limit()
            
            logger.debug(f"Geocoding query: {query}")
            location = self.geocoder.geocode(query)
            
            if location is None:
                logger.warning(f"No results found for query: {query}")
                return None
            
            result = GeocodingResult(
                latitude=location.latitude,
                longitude=location.longitude,
                address=location.address,
                raw_data={
                    "raw": location.raw,
                    "point": location.point,
                },
                provider=self.name,
                confidence=0.8,  # Nominatim doesn't provide confidence scores
            )
            
            logger.debug(f"Geocoding successful: {result}")
            return result
            
        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for query: {query}")
            return None
        except GeocoderUnavailable:
            logger.error(f"Geocoding service unavailable for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Geocoding error for query '{query}': {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodingResult]:
        """Reverse geocode coordinates using Nominatim.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        try:
            self._rate_limit()
            
            logger.debug(f"Reverse geocoding coordinates: ({latitude}, {longitude})")
            location = self.geocoder.reverse((latitude, longitude))
            
            if location is None:
                logger.warning(f"No results found for coordinates: ({latitude}, {longitude})")
                return None
            
            result = GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                address=location.address,
                raw_data={
                    "raw": location.raw,
                    "point": location.point,
                },
                provider=self.name,
                confidence=0.8,
            )
            
            logger.debug(f"Reverse geocoding successful: {result}")
            return result
            
        except GeocoderTimedOut:
            logger.error(f"Reverse geocoding timeout for coordinates: ({latitude}, {longitude})")
            return None
        except GeocoderUnavailable:
            logger.error(f"Reverse geocoding service unavailable for coordinates: ({latitude}, {longitude})")
            return None
        except Exception as e:
            logger.error(f"Reverse geocoding error for coordinates ({latitude}, {longitude}): {e}")
            return None


class GeocodingService:
    """Main geocoding service with provider management and caching.
    
    This service manages multiple geocoding providers and implements
    caching, fallback logic, and error handling.
    
    Attributes:
        providers: List of available geocoding providers
        cache_enabled: Whether caching is enabled
        default_provider: Name of the default provider
    """
    
    def __init__(self, providers: Optional[List[GeocodingProvider]] = None, cache_enabled: bool = True):
        """Initialize the geocoding service.
        
        Args:
            providers: List of geocoding providers to use
            cache_enabled: Whether to enable caching (default: True)
        """
        self.providers = providers or []
        self.cache_enabled = cache_enabled
        self.default_provider = None
        
        # Set up default providers if none provided
        if not self.providers:
            self._setup_default_providers()
    
    def _setup_default_providers(self) -> None:
        """Set up default geocoding providers."""
        # Add Nominatim as the default provider
        nominatim = NominatimProvider(
            rate_limit_per_minute=getattr(settings, 'GEOCODING_RATE_LIMIT_PER_MINUTE', 60)
        )
        self.providers.append(nominatim)
        self.default_provider = "nominatim"
        
        logger.info(f"Initialized geocoding service with {len(self.providers)} providers")
    
    def add_provider(self, provider: GeocodingProvider) -> None:
        """Add a new geocoding provider.
        
        Args:
            provider: Geocoding provider instance to add
        """
        self.providers.append(provider)
        logger.info(f"Added geocoding provider: {provider.name}")
    
    def get_provider(self, name: str) -> Optional[GeocodingProvider]:
        """Get a provider by name.
        
        Args:
            name: Provider name to find
            
        Returns:
            GeocodingProvider if found, None otherwise
        """
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None
    
    def geocode(self, query: str, provider_name: Optional[str] = None) -> Optional[GeocodingResult]:
        """Geocode an address using the specified or default provider.
        
        Args:
            query: Address string to geocode
            provider_name: Name of provider to use (uses default if None)
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        if not self.providers:
            logger.error("No geocoding providers available")
            return None
        
        # Check cache first if enabled
        if self.cache_enabled:
            try:
                from directory.models import GeocodingCache
                cached_result = GeocodingCache.get_cached_result(query, provider_name)
                if cached_result:
                    logger.info(f"Cache hit for query: {query}")
                    return GeocodingResult(
                        latitude=cached_result.latitude,
                        longitude=cached_result.longitude,
                        address=cached_result.address,
                        raw_data={
                            "cached": True,
                            "provider": cached_result.provider,
                            "confidence": cached_result.confidence,
                        },
                        provider=cached_result.provider,
                        confidence=cached_result.confidence,
                        cache_hit=True,
                    )
            except Exception as e:
                logger.warning(f"Cache lookup failed for query '{query}': {e}")
        
        # Try to get the specified provider
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider:
                result = provider.geocode(query)
                if result:
                    # Cache the result if caching is enabled
                    if self.cache_enabled:
                        self._cache_result(query, result)
                    return result
                logger.warning(f"Provider {provider_name} failed, trying others")
        
        # Try all providers in order
        for provider in self.providers:
            try:
                result = provider.geocode(query)
                if result and result.is_valid():
                    logger.info(f"Geocoding successful with provider {provider.name}")
                    # Cache the result if caching is enabled
                    if self.cache_enabled:
                        self._cache_result(query, result)
                    return result
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                continue
        
        logger.error(f"All geocoding providers failed for query: {query}")
        return None
    
    def _cache_result(self, query: str, result: GeocodingResult) -> None:
        """Cache a geocoding result.
        
        Args:
            query: The original geocoding query
            result: The geocoding result to cache
        """
        try:
            from directory.models import GeocodingCache
            
            # Determine cache duration based on confidence
            cache_duration_hours = 24  # Default 24 hours
            if result.confidence:
                if result.confidence >= 0.9:
                    cache_duration_hours = 168  # 1 week for high confidence
                elif result.confidence >= 0.7:
                    cache_duration_hours = 72   # 3 days for medium confidence
                else:
                    cache_duration_hours = 12   # 12 hours for low confidence
            
            GeocodingCache.store_result(
                query=query,
                latitude=result.latitude,
                longitude=result.longitude,
                address=result.address,
                provider=result.provider,
                confidence=result.confidence,
                cache_duration_hours=cache_duration_hours
            )
            
            logger.debug(f"Cached geocoding result for query: {query}")
            
        except Exception as e:
            logger.warning(f"Failed to cache geocoding result for query '{query}': {e}")
    
    def reverse_geocode(self, latitude: float, longitude: float, provider_name: Optional[str] = None) -> Optional[GeocodingResult]:
        """Reverse geocode coordinates using the specified or default provider.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            provider_name: Name of provider to use (uses default if None)
            
        Returns:
            GeocodingResult if successful, None if failed
        """
        if not self.providers:
            logger.error("No geocoding providers available")
            return None
        
        # Try to get the specified provider
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider:
                result = provider.reverse_geocode(latitude, longitude)
                if result:
                    return result
                logger.warning(f"Provider {provider_name} failed, trying others")
        
        # Try all providers in order
        for provider in self.providers:
            try:
                result = provider.reverse_geocode(latitude, longitude)
                if result and result.is_valid():
                    logger.info(f"Reverse geocoding successful with provider {provider.name}")
                    return result
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                continue
        
        logger.error(f"All reverse geocoding providers failed for coordinates: ({latitude}, {longitude})")
        return None
    
    def batch_geocode(self, queries: List[str], provider_name: Optional[str] = None) -> List[Optional[GeocodingResult]]:
        """Geocode multiple addresses in batch.
        
        Args:
            queries: List of address strings to geocode
            provider_name: Name of provider to use (uses default if None)
            
        Returns:
            List of GeocodingResult objects (None for failed queries)
        """
        results = []
        for query in queries:
            result = self.geocode(query, provider_name)
            results.append(result)
        return results


# Convenience function for easy access
def get_geocoding_service() -> GeocodingService:
    """Get a configured geocoding service instance.
    
    Returns:
        GeocodingService instance with default providers
    """
    return GeocodingService()
