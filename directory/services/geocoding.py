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
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from urllib.parse import quote
from functools import wraps

import requests
from django.conf import settings

# Only import geopy modules if GIS is enabled
if getattr(settings, "GIS_ENABLED", False):
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
    from geopy.geocoders import Nominatim
else:
    # Create dummy classes for when GIS is disabled
    class GeocoderTimedOut(Exception):
        pass

    class GeocoderUnavailable(Exception):
        pass

    class Nominatim:
        def __init__(self, *args, **kwargs):
            pass


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
            -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
            and self.latitude != 0
            or self.longitude != 0
        )


class CircuitBreaker:
    """Circuit breaker pattern for protecting against cascading failures.

    This class implements a circuit breaker pattern that monitors the success/failure
    of operations and can temporarily disable a service when it's failing too often.

    Attributes:
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds to wait before attempting recovery
        expected_exception: Exception type that indicates a failure
        last_failure_time: Timestamp of the last failure
        failure_count: Number of consecutive failures
        state: Current state of the circuit breaker
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before attempting recovery
            expected_exception: Exception type that indicates a failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.last_failure_time = 0
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if successful

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker attempting recovery")
            else:
                raise Exception(f"Circuit breaker is OPEN for {self.name}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.debug("Circuit breaker: Operation successful")

    def _on_failure(self) -> None:
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
        else:
            logger.debug(
                f"Circuit breaker: Failure {self.failure_count}/{self.failure_threshold}"
            )


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # Add jitter if enabled
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    time.sleep(delay)

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


class TextBasedLocationMatcher:
    """Text-based location matching as a fallback when geocoding fails.

    This class provides text-based location matching using CoverageArea data
    when geocoding services are unavailable or fail.
    """

    def __init__(self):
        """Initialize the text-based location matcher."""
        self._coverage_areas_cache = None
        self._last_cache_update = 0
        self._cache_ttl = 300  # 5 minutes

    def _get_coverage_areas(self) -> List[Dict]:
        """Get coverage areas for text matching.

        Returns:
            List of coverage area dictionaries with name and kind
        """
        current_time = time.time()

        # Refresh cache if expired
        if (
            self._coverage_areas_cache is None
            or current_time - self._last_cache_update > self._cache_ttl
        ):
            try:
                from directory.models import CoverageArea

                areas = CoverageArea.objects.values("name", "kind", "ext_ids")
                self._coverage_areas_cache = list(areas)
                self._last_cache_update = current_time
                logger.debug(
                    f"Cached {len(self._coverage_areas_cache)} coverage areas for text matching"
                )
            except Exception as e:
                logger.warning(f"Failed to load coverage areas for text matching: {e}")
                self._coverage_areas_cache = []

        return self._coverage_areas_cache

    def find_location_match(self, query: str) -> Optional[GeocodingResult]:
        """Find a location match using text-based matching.

        Args:
            query: Location query string

        Returns:
            GeocodingResult if a match is found, None otherwise
        """
        if not query:
            return None

        query_lower = query.lower().strip()
        coverage_areas = self._get_coverage_areas()

        # Try exact matches first
        for area in coverage_areas:
            area_name = area["name"].lower()
            if query_lower == area_name:
                logger.info(f"Text-based exact match found: {area['name']}")
                return self._create_result_from_area(area, query, confidence=0.9)

        # Try partial matches
        for area in coverage_areas:
            area_name = area["name"].lower()
            if query_lower in area_name or area_name in query_lower:
                logger.info(f"Text-based partial match found: {area['name']}")
                return self._create_result_from_area(area, query, confidence=0.7)

        # Try matching against ext_ids (FIPS codes, etc.)
        for area in coverage_areas:
            ext_ids = area.get("ext_ids", {})
            for key, value in ext_ids.items():
                if isinstance(value, str) and query_lower in value.lower():
                    logger.info(
                        f"Text-based ext_id match found: {area['name']} ({key}={value})"
                    )
                    return self._create_result_from_area(area, query, confidence=0.6)

        logger.debug(f"No text-based match found for query: {query}")
        return None

    def _create_result_from_area(
        self, area: Dict, original_query: str, confidence: float
    ) -> GeocodingResult:
        """Create a GeocodingResult from a coverage area.

        Args:
            area: Coverage area dictionary
            original_query: Original query string
            confidence: Confidence score for the match

        Returns:
            GeocodingResult with area information
        """
        # For text-based matching, we don't have exact coordinates
        # We'll use a default location (center of the area if available)
        # This is a simplified approach - in a real implementation,
        # you might want to store center coordinates in CoverageArea

        # Use a default location (this could be enhanced with actual area centers)
        default_lat = 37.7749  # Default to a reasonable location
        default_lon = -122.4194

        return GeocodingResult(
            latitude=default_lat,
            longitude=default_lon,
            address=f"{area['name']} (text-based match)",
            raw_data={
                "text_match": True,
                "area_name": area["name"],
                "area_kind": area["kind"],
                "ext_ids": area.get("ext_ids", {}),
                "original_query": original_query,
            },
            provider="text_matcher",
            confidence=confidence,
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
    def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[GeocodingResult]:
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
        circuit_breaker: Circuit breaker for protecting against failures
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

        # Initialize circuit breaker for this provider
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120,  # 2 minutes
            expected_exception=(
                GeocoderTimedOut,
                GeocoderUnavailable,
                requests.RequestException,
            ),
        )

    @property
    def geocoder(self) -> Nominatim:
        """Get or create the Nominatim geocoder instance."""
        if self._geocoder is None:
            self._geocoder = Nominatim(user_agent=self.user_agent, timeout=self.timeout)
        return self._geocoder

    @retry_with_backoff(
        max_retries=2,
        base_delay=1.0,
        max_delay=10.0,
        exceptions=(GeocoderTimedOut, GeocoderUnavailable, requests.RequestException),
    )
    def _geocode_with_retry(self, query: str) -> Optional[GeocodingResult]:
        """Internal geocoding method with retry logic.

        Args:
            query: Address string to geocode

        Returns:
            GeocodingResult if successful, None if failed
        """
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

    def geocode(self, query: str) -> Optional[GeocodingResult]:
        """Geocode an address using Nominatim with circuit breaker protection.

        Args:
            query: Address string to geocode

        Returns:
            GeocodingResult if successful, None if failed
        """
        try:
            return self.circuit_breaker.call(self._geocode_with_retry, query)
        except Exception as e:
            logger.error(f"Geocoding failed for query '{query}' (circuit breaker): {e}")
            return None

    @retry_with_backoff(
        max_retries=2,
        base_delay=1.0,
        max_delay=10.0,
        exceptions=(GeocoderTimedOut, GeocoderUnavailable, requests.RequestException),
    )
    def _reverse_geocode_with_retry(
        self, latitude: float, longitude: float
    ) -> Optional[GeocodingResult]:
        """Internal reverse geocoding method with retry logic.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult if successful, None if failed
        """
        self._rate_limit()

        logger.debug(f"Reverse geocoding coordinates: ({latitude}, {longitude})")
        location = self.geocoder.reverse((latitude, longitude))

        if location is None:
            logger.warning(
                f"No results found for coordinates: ({latitude}, {longitude})"
            )
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

    def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[GeocodingResult]:
        """Reverse geocode coordinates using Nominatim with circuit breaker protection.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodingResult if successful, None if failed
        """
        try:
            return self.circuit_breaker.call(
                self._reverse_geocode_with_retry, latitude, longitude
            )
        except Exception as e:
            logger.error(
                f"Reverse geocoding failed for coordinates ({latitude}, {longitude}) (circuit breaker): {e}"
            )
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

    def __init__(
        self,
        providers: Optional[List[GeocodingProvider]] = None,
        cache_enabled: bool = True,
    ):
        """Initialize the geocoding service.

        Args:
            providers: List of geocoding providers to use
            cache_enabled: Whether to enable caching (default: True)
        """
        self.providers = providers or []
        self.cache_enabled = cache_enabled
        self.default_provider = None

        # Initialize text-based location matcher for fallback
        self.text_matcher = TextBasedLocationMatcher()

        # Set up default providers if none provided
        if not self.providers:
            self._setup_default_providers()

    def _setup_default_providers(self) -> None:
        """Set up default geocoding providers."""
        # Add Nominatim as the default provider
        nominatim = NominatimProvider(
            rate_limit_per_minute=getattr(
                settings, "GEOCODING_RATE_LIMIT_PER_MINUTE", 60
            )
        )
        self.providers.append(nominatim)
        self.default_provider = "nominatim"

        # Note: Additional providers like Google Maps can be added here if API keys are available
        # For now, we use Nominatim (free) + text-based fallback for robust geocoding

        logger.info(
            f"Initialized geocoding service with {len(self.providers)} providers"
        )

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

    def geocode(
        self, query: str, provider_name: Optional[str] = None
    ) -> Optional[GeocodingResult]:
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

        # Try text-based location matching as fallback
        logger.info(
            f"All geocoding providers failed, trying text-based matching for query: {query}"
        )
        text_result = self.text_matcher.find_location_match(query)
        if text_result:
            logger.info(f"Text-based location match found for query: {query}")
            # Cache the text-based result with shorter duration
            if self.cache_enabled:
                self._cache_result(query, text_result)
            return text_result

        logger.error(f"All geocoding methods failed for query: {query}")
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
                    cache_duration_hours = 72  # 3 days for medium confidence
                else:
                    cache_duration_hours = 12  # 12 hours for low confidence

            GeocodingCache.store_result(
                query=query,
                latitude=result.latitude,
                longitude=result.longitude,
                address=result.address,
                provider=result.provider,
                confidence=result.confidence,
                cache_duration_hours=cache_duration_hours,
            )

            logger.debug(f"Cached geocoding result for query: {query}")

        except Exception as e:
            logger.warning(f"Failed to cache geocoding result for query '{query}': {e}")

    def reverse_geocode(
        self, latitude: float, longitude: float, provider_name: Optional[str] = None
    ) -> Optional[GeocodingResult]:
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
                    logger.info(
                        f"Reverse geocoding successful with provider {provider.name}"
                    )
                    return result
            except Exception as e:
                logger.error(f"Provider {provider.name} failed: {e}")
                continue

        logger.error(
            f"All reverse geocoding providers failed for coordinates: ({latitude}, {longitude})"
        )
        return None

    def batch_geocode(
        self, queries: List[str], provider_name: Optional[str] = None
    ) -> List[Optional[GeocodingResult]]:
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
