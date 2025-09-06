"""
Data models for the resource verification system.

This module contains dataclasses that represent the core data structures
used in the verification process, providing type safety and better
code organization.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class WebsiteDiscoveryResult:
    """
    Result of website discovery process.

    Attributes:
        status: Status of the discovery process ('success', 'error')
        message: Human-readable message about the result
        urls_found: Number of URLs discovered
        discovered_urls: List of discovered URL information
        tool_calls_count: Number of tool calls made during discovery
        duration_ms: Time taken for discovery in milliseconds
        timestamp: When the discovery was performed
        search_strategy: Description of the search approach used
        entity_resolution: Information about entity name resolution
        total_urls: Total URLs found (including duplicates)
        search_notes: Any notes about the discovery process
    """
    status: str
    message: str
    urls_found: int = 0
    discovered_urls: List[Dict[str, Any]] = None
    tool_calls_count: int = 0
    duration_ms: int = 0
    timestamp: str = ""
    search_strategy: str = ""
    entity_resolution: Dict[str, Any] = None
    total_urls: int = 0
    search_notes: str = ""

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.discovered_urls is None:
            self.discovered_urls = []
        if self.entity_resolution is None:
            self.entity_resolution = {}


@dataclass
class ResourceData:
    """
    Formatted resource data for verification.

    Attributes:
        id: Resource ID
        name: Resource name
        status: Resource status
        category: Resource category name
        description: Resource description
        city: Resource city
        state: Resource state
        county: Resource county
        verification_status: Verification status information
        service_areas: Service area information
        service_types: Service type information
        contact_information: Contact details (verbose mode)
        operational_details: Operational information (verbose mode)
        service_details: Service-specific details (verbose mode)
        metadata: Metadata information (verbose mode)
    """
    id: int
    name: str
    status: str
    category: Optional[str]
    description: str
    city: str
    state: str
    county: str
    verification_status: Dict[str, Any]
    service_areas: Dict[str, Any]
    service_types: Dict[str, Any]
    contact_information: Optional[Dict[str, Any]] = None
    operational_details: Optional[Dict[str, Any]] = None
    service_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize optional fields."""
        if self.contact_information is None:
            self.contact_information = {}
        if self.operational_details is None:
            self.operational_details = {}
        if self.service_details is None:
            self.service_details = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VerificationResult:
    """
    Result of a verification operation.

    Attributes:
        resource_id: ID of the resource being verified
        resource_name: Name of the resource
        status: Verification status ('success', 'error', 'pending')
        message: Human-readable result message
        website_discovery: Website discovery results
        timestamp: When verification was performed
        verified_by: User who performed verification
        notes: Additional verification notes
    """
    resource_id: int
    resource_name: str
    status: str
    message: str
    website_discovery: Optional[WebsiteDiscoveryResult] = None
    timestamp: str = ""
    verified_by: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        """Initialize optional fields."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class FieldVerificationResult:
    """
    Result of field-by-field verification process.
    
    Attributes:
        status: Status of the verification ('success', 'error')
        message: Human-readable message about the result
        fields_verified: Number of fields verified
        field_results: List of individual field verification results
        tool_calls_count: Number of tool calls made during verification
        duration_ms: Time taken for verification in milliseconds
        timestamp: When verification was performed
        verification_strategy: Description of the verification approach
        total_fields: Total fields checked
        verification_notes: Any notes about the verification process
        resource_name: Verified resource name
        category: Verified category with ID
        description: Verified description
        location: Verified location information
        contact_info: Verified contact information
        sources: List of source URLs used for verification
    """
    status: str
    message: str
    fields_verified: int = 0
    field_results: List[Dict[str, Any]] = None
    tool_calls_count: int = 0
    duration_ms: int = 0
    timestamp: str = ""
    verification_strategy: str = ""
    total_fields: int = 0
    verification_notes: str = ""
    resource_name: str = ""
    category: str = ""
    description: str = ""
    location: str = ""
    contact_info: Dict[str, Any] = None
    sources: List[str] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.field_results is None:
            self.field_results = []
        if self.contact_info is None:
            self.contact_info = {}
        if self.sources is None:
            self.sources = []


@dataclass
class CursorAgentResult:
    """
    Result from Cursor Agent execution.

    Attributes:
        success: Whether the execution was successful
        error: Error message if execution failed
        full_text: Complete text output from Cursor Agent
        duration_ms: Time taken for execution
        tool_calls: List of tool calls made during execution
        parsed_data: Parsed data from the response
    """
    success: bool
    error: Optional[str] = None
    full_text: str = ""
    duration_ms: int = 0
    tool_calls: List[Dict[str, Any]] = None
    parsed_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.tool_calls is None:
            self.tool_calls = []
        if self.parsed_data is None:
            self.parsed_data = {}

