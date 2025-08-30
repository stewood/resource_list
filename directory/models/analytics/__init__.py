"""
Analytics Models Package - Search and Audit Models

This package contains models related to analytics and audit functionality:
- SearchAnalytics: Search analytics and metrics
- LocationSearchLog: Log of location-based searches
- AuditLog: Audit trail for resource changes
- ResourceVersion: Version history for resources

Author: Resource Directory Team
Created: 2024
Last Modified: 2025-01-15
Version: 1.0.0
"""

from .search_analytics import SearchAnalytics, LocationSearchLog
from .audit import AuditLog, ResourceVersion

__all__ = [
    "SearchAnalytics",
    "LocationSearchLog",
    "AuditLog",
    "ResourceVersion",
]
