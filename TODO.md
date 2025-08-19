# Spec: Add SpatiaLite Service Areas to Resource List (Post‑fork Plan)

## 0) Goals & Non‑Goals

**Goals**

* Enable location‑based eligibility: given a person's address/lat‑lon, return resources whose **service areas** include that point.
* Support multiple service‑area types per resource: **City, County, State, Custom Polygon**, and **Radius from a point**.
* Keep the current SQLite stack; add **SpatiaLite + GeoDjango** for spatial queries.
* Provide a staff‑friendly **Service Area Manager** UI (autocomplete + map draw + radius) consistent with the project's HTMX + Bootstrap patterns.

**Non‑Goals (Phase 1)**

* Multi‑tenant separation, advanced policy/precedence rules, or complex routing logic.
* Global geocoding or batch address normalization beyond a single provider + caching.
* Full PostGIS migration (considered later).

---

## 1) Architecture & Dependencies

* **Database**: SQLite with SpatiaLite extension.
* **Django**: Enable `django.contrib.gis`. Switch DB engine to `django.contrib.gis.db.backends.spatialite`.
* **GIS libs**: GDAL/OGR (runtime import), GEOS; Python deps: `django`, `django.contrib.gis`, optional `shapely` for utilities.
* **Frontend map**: Leaflet + `leaflet.draw`; optional `leaflet-geosearch`.
* **Geocoding**: Nominatim (OSM) in dev, with abstraction for Mapbox/Google in prod. Add simple cache table.

**Config**

* `SPATIALITE_LIBRARY_PATH` (env-based); settings toggle `GIS_ENABLED=True/False` for local dev where SpatiaLite may not be present.

---

## 2) Data Model Additions

```text
CoverageArea
- id (pk)
- kind: ENUM[ CITY, COUNTY, STATE, POLYGON, RADIUS ]
- name: str (e.g., "Laurel County, KY")
- geom: MultiPolygon (SRID 4326) — for all non-radius coverage; for RADIUS we store the **buffer polygon** too
- center: Point (SRID 4326, nullable) — used for radius authoring only
- radius_m: int (nullable) — authoring; buffer stored in geom
- ext_ids: JSON (e.g., {"state_fips":"21", "county_fips":"125"})
- created_by, updated_by, timestamps

Resource (existing)
- M2M: Resource.coverage_areas -> CoverageArea (through table for audit)

Through model (audit)
- id
- resource_id
- coverage_area_id
- created_by, created_at
```

**Indexes**

* Spatial index on `CoverageArea.geom` (R-Tree via SpatiaLite)
* B-Tree on `kind`, `ext_ids` (JSON path where supported or string key fields)

**Notes**

* Store radius **as a polygon buffer** in `geom` to unify queries (all use `geom__contains`).

---

## 3) Ingestion & Boundary Sources

**Primary**: U.S. Census TIGER/Line (counties, states). Optional: OSM boundaries for cities/places.

### Management Commands

* `import_counties --state KY [--year 2024]`

  * Downloads TIGER county shapefile for state; converts to GeoJSON WGS84; creates/updates `CoverageArea` rows with `kind=COUNTY`, `ext_ids` (state\_fips, county\_fips), `name`.
* `import_states [--year 2024]`
* `import_places --state KY` (optional for cities)
* `load_geojson <path> --kind POLYGON --name "Custom Area"` (admin utility)

**Validation**

* Ensure SRID=4326; fix winding if needed; dissolve multiparts per area; simplify geometry for display assets (TopoJSON) while keeping full fidelity in DB.

---

## 4) Query Flow (Runtime)

1. **Geocode** input → `(lat, lon)`; cache by normalized address string.
2. Build `Point(lon, lat, srid=4326)`.
3. Query resources with a single ORM filter:

   * `Resource.objects.filter(coverage_areas__geom__contains=point).distinct()`
4. (Optional) Annotate specificity badges by `CoverageArea.kind` for display.
5. (Optional) Sort by specificity (RADIUS > CITY > COUNTY > STATE) and proximity to resource location when available.

**Edge Cases**

* Overlapping areas (return all).
* Near-boundary points (accept database truth; future: tolerance/snap rules if required).

---

## 5) Admin & Staff UI

### A) Resource Create/Edit

* Step 1: Resource details (existing flow).
* Step 2: **Service Areas**

  * Embed **Service Area Manager** modal/component.

### B) Service Area Manager (Modal/Page)

**Tabs**

1. **Find Boundary** (County/City/State)

   * Autocomplete by name; list shows name + code (e.g., FIPS);
   * On add → draw boundary on map and add chip in "Selected".
2. **Radius**

   * Map click sets `center`; slider (0.5–100 mi/km) → preview circle;
   * On save → buffer to polygon (server), persist as `geom` with `kind=RADIUS`.
3. **Custom Polygon**

   * Draw polygon via `leaflet.draw`; name it; save as `POLYGON`.
4. **Upload**

   * Drag‑drop GeoJSON; validate SRID; show preview; save.

**Selected list**

* Chips/table of chosen areas with badges (kind), actions: Preview, Edit (radius/custom), Remove.

**Validation**

* Prevent self‑intersecting polygons; limit vertex count; enforce SRID 4326.

---

## 6) API/Views (HTMX endpoints)

* `GET /areas/search?kind=COUNTY&q=laurel` → JSON list with `id,name,kind,ext_ids,bounds`.
* `POST /areas/radius` → `{center:{lat,lon}, radius:{m}}` → returns created `CoverageArea` (buffered polygon stored in `geom`).
* `POST /areas/polygon` → GeoJSON Feature → returns created `CoverageArea`.
* `POST /resources/{id}/areas` → attach/detach coverage areas.

Security: staff‑only permissions; CSRF via standard Django; rate‑limit geocoding endpoint.

---

## 7) Migrations & Backward Compatibility

* New GIS fields in fresh migrations; feature flag: if `GIS_ENABLED=False`, hide UI and skip GIS queries (fallback behavior: no area filtering or use city/county text fields if present).
* Data backfill: none required for existing resources; admins can attach areas over time.

---

## 8) Testing Plan

* Unit tests: model save (radius buffer creation), polygon validation, `geom__contains` logic.
* Integration: import one state's counties; attach areas; query with test addresses.
* Edge: points exactly on boundary; overlapping areas; deleting attached areas.

---

## 9) Performance & Ops

* Spatial index on `geom`; ensure R‑Tree built.
* Geometry simplification for frontend (precompute simplified GeoJSON/TopoJSON for map preview).
* Geocoding cache table; configurable provider + API key.
* Observability: log query timings; add health check for SpatiaLite extension presence.

---

## 10) Rollout Plan

1. Fork project; create feature branch `feature/spatial-service-areas`.
2. Add GIS deps & settings; gated by `GIS_ENABLED` env var.
3. Add models + migrations; write import commands.
4. Build Service Area Manager UI (hidden behind feature flag initially).
5. Seed 1–2 counties (e.g., **Laurel County, KY**) for demo.
6. Implement query path in search endpoint; add badges in results.
7. QA with boundary fixtures; fix edge cases.
8. Enable feature in staging → production.

---

## 11) Future Enhancements

* PostGIS migration for concurrency/scale.
* H3 hex‑index caching for ultra‑fast lookups.
* Saved searches & shareable filter URLs including coverage filters.
* Data governance: export redaction for PII in CSV/GeoJSON.
* Sync jobs to refresh TIGER/OSM geometries annually.
