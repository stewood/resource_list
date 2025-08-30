# API Documentation

## Overview

This document provides comprehensive documentation for all API endpoints in the Resource Directory system. The API is built using Django REST Framework and provides RESTful endpoints for coverage area management, location-based search, and resource management.

## Base URL

All API endpoints are relative to the base URL of your application.

## Authentication

Most endpoints are public, but some require authentication:
- **Public endpoints**: No authentication required
- **Protected endpoints**: Require user authentication (session-based)

## Common Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
    "success": true,
    "data": { ... },
    "pagination": { ... }  // if applicable
}
```

### Error Response
```json
{
    "error": "Error message description",
    "status": 400
}
```

## API Endpoints

### 1. Area Search API

#### GET /api/areas/search/

Search for coverage areas by kind and name.

**Query Parameters:**
- `kind` (optional): Coverage area kind (STATE, COUNTY, CITY, POLYGON, RADIUS)
- `q` (optional): Search query for area names
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Number of results per page (default: 20, max: 100)

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "name": "Kentucky",
            "kind": "STATE",
            "ext_ids": {
                "state_fips": "21",
                "state_name": "Kentucky"
            },
            "bounds": {
                "north": 39.1,
                "south": 36.5,
                "east": -81.9,
                "west": -89.6
            }
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_count": 1,
        "total_pages": 1
    }
}
```

#### GET /api/areas/{area_id}/preview/

Get preview information for a specific coverage area.

**Path Parameters:**
- `area_id`: ID of the coverage area

**Response:**
```json
{
    "id": 1,
    "name": "Kentucky",
    "kind": "STATE",
    "ext_ids": { ... },
    "bounds": { ... },
    "resource_count": 45
}
```

### 2. Location-Based Search API

#### GET /api/search/by-location/

Find resources by location using address geocoding or coordinates.

**Query Parameters:**
- `address` (optional): Address string to geocode and search
- `lat` (optional): Latitude coordinate (required if no address)
- `lon` (optional): Longitude coordinate (required if no address)
- `radius_miles` (optional): Search radius in miles (default: 10, max: 100)
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Number of results per page (default: 20)

**Response:**
```json
{
    "location": {
        "address": "London, KY",
        "coordinates": [37.1283, -84.0836],
        "geocoded": true
    },
    "results": [
        {
            "id": 1,
            "name": "Crisis Intervention Center",
            "description": "24/7 crisis intervention services",
            "city": "London",
            "state": "KY",
            "coverage_areas": ["Kentucky", "Laurel County"],
            "distance_miles": 0.5
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_count": 1,
        "total_pages": 1
    }
}
```

### 3. Resource Area Management API

#### GET /api/resources/{resource_id}/areas/

Get all coverage areas associated with a resource.

**Path Parameters:**
- `resource_id`: ID of the resource

**Response:**
```json
{
    "resource_id": 123,
    "resource_name": "Crisis Intervention Center",
    "coverage_areas": [
        {
            "id": 156,
            "name": "Laurel County",
            "kind": "COUNTY",
            "ext_ids": { ... }
        }
    ],
    "total_count": 1
}
```

#### POST /api/resources/{resource_id}/areas/

Manage resource-coverage area associations. **Requires authentication.**

**Path Parameters:**
- `resource_id`: ID of the resource

**Request Body:**
```json
{
    "action": "attach|detach|replace",
    "coverage_area_ids": [1, 2, 3],
    "notes": "Optional notes about the association"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Areas attached successfully",
    "attached_count": 2,
    "detached_count": 1,
    "errors": []
}
```

### 4. Resource Eligibility API

#### GET /api/resources/{resource_id}/eligibility/

Check if a resource serves a specific location.

**Path Parameters:**
- `resource_id`: ID of the resource

**Query Parameters:**
- `lat` (required): Latitude coordinate
- `lon` (required): Longitude coordinate
- `address` (optional): Address string for display purposes

**Response:**
```json
{
    "resource_id": 123,
    "resource_name": "Crisis Intervention Center",
    "serves_location": true,
    "distance_miles": 2.5,
    "eligibility_reason": "Location is within Laurel County (COUNTY)",
    "coverage_areas": [
        {
            "id": 156,
            "name": "Laurel County",
            "kind": "COUNTY",
            "distance_miles": 0.0,
            "contains_location": true
        }
    ]
}
```

### 5. Reverse Geocoding API

#### GET /api/geocode/reverse/

Convert coordinates to human-readable addresses.

**Query Parameters:**
- `lat` (required): Latitude coordinate
- `lon` (required): Longitude coordinate

**Response:**
```json
{
    "success": true,
    "result": {
        "address": "London, Laurel County, Kentucky, United States",
        "latitude": 37.1283343,
        "longitude": -84.0835576,
        "confidence": 0.8,
        "provider": "nominatim"
    }
}
```

### 6. States and Counties API

#### GET /api/location/states-counties/

Get states and counties for dropdowns.

**Query Parameters:**
- `state_fips` (optional): State FIPS code (for getting counties)

**Response:**
```json
{
    "success": true,
    "states": [
        {
            "id": 123,
            "name": "Kentucky",
            "ext_ids": {
                "state_fips": "21"
            }
        }
    ],
    "counties": [
        {
            "id": 456,
            "name": "Laurel County",
            "ext_ids": {
                "state_fips": "21",
                "county_fips": "125"
            }
        }
    ]
}
```

### 7. AI Verification API

#### POST /api/resources/{resource_id}/ai-verify/

Trigger AI verification for a resource. **Requires authentication.**

**Path Parameters:**
- `resource_id`: ID of the resource

**Response:**
```json
{
    "success": true,
    "verification_id": "ver_123456",
    "status": "pending",
    "message": "AI verification started"
}
```

### 8. AI Dashboard API

#### GET /api/resources/{resource_id}/ai-dashboard/

Get AI dashboard data for a resource.

**Path Parameters:**
- `resource_id`: ID of the resource

**Response:**
```json
{
    "resource_id": 123,
    "ai_verifications": [
        {
            "id": "ver_123456",
            "status": "completed",
            "created_at": "2025-08-30T11:00:00Z",
            "results": { ... }
        }
    ]
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

## Rate Limiting

API endpoints are subject to rate limiting to prevent abuse. Limits are applied per IP address and user session.

## Dependencies

The API depends on the following services:
- **Geocoding Service**: For address geocoding and reverse geocoding
- **Spatial Database**: For geographic queries and distance calculations
- **Authentication System**: For protected endpoints

## Versioning

This API is currently at version 1.0. Future versions will maintain backward compatibility where possible.

## Support

For API support or questions, please refer to the project documentation or contact the development team.
