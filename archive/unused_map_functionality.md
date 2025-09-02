# Unused Map Functionality - Archived

## Overview
This file documents the map-related functionality that was removed from the service area management system because it is no longer used.

## Removed Functions

### Map Initialization Functions
- `initializeMaps()` - Initialized boundary, radius, polygon, and upload maps
- `initializeMapForTab()` - Set up maps for specific tabs
- `cleanupMaps()` - Cleaned up map instances when modal was hidden

### Map Display Functions  
- `displayExistingAreasOnMap()` - Displayed service areas as colored rectangles on map
- `displaySearchResultsOnMap()` - Showed search results on the map
- `displayRadiusOnMap()` - Displayed radius-based service areas
- `displayPolygonOnMap()` - Displayed polygon-based service areas

### Map Interaction Functions
- `previewServiceArea()` - Preview service area on map
- `removeServiceAreaFromMap()` - Remove service area from map display
- `fitMapToAreas()` - Adjust map view to show all areas

### Map Utility Functions
- `getMapBounds()` - Get current map boundaries
- `setMapView()` - Set map center and zoom level
- `addMapControls()` - Add map control buttons
- `removeMapLayers()` - Clean up map layers

## Map Libraries Used
- Leaflet.js for interactive maps
- Mapbox or OpenStreetMap tiles for map data
- Drawing tools for creating custom areas

## Why Removed
- Map functionality was not being used by editors/reviewers
- Simplified service area management was preferred
- Map complexity was causing maintenance overhead
- Focus shifted to simple dropdown-based area selection

## Files Modified
- `templates/directory/resource_form.html` - Removed map-related JavaScript functions
- `static/theme.js` - Removed map initialization code
- CSS classes for map styling removed

## Data Structure Impact
- `selectedServiceAreas` array still used for enhanced service area manager
- `serviceAreas` array used for simplified form display
- Both arrays need to be synchronized for proper functionality

## Archive Date
2025-09-02 - Removed during service area management cleanup
