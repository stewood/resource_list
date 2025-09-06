# Geographic Import Commands

These commands are used for importing and updating geographic data (states, counties, cities) from TIGER/Line data sources. They are actively used by the geographic data management scripts in `scripts/geo/operations/`.

## 📁 Available Commands

### `import_states_enhanced.py`
- **Purpose**: Import state-level geographic data with enhanced metadata
- **When Used**: Initial setup and ongoing updates of state boundaries
- **Dependencies**: TIGER/Line data files
- **Usage**: `python manage.py import_states_enhanced --states KY --year 2023`

### `import_cities_enhanced.py`
- **Purpose**: Import city-level geographic data with enhanced metadata
- **When Used**: Initial setup and ongoing updates of city boundaries
- **Dependencies**: TIGER/Line data files
- **Usage**: `python manage.py import_cities_enhanced --states KY --year 2023`

### `import_counties_enhanced.py`
- **Purpose**: Import county-level geographic data with enhanced metadata
- **When Used**: Initial setup and ongoing updates of county boundaries
- **Dependencies**: TIGER/Line data files
- **Usage**: `python manage.py import_counties_enhanced --states KY --year 2023`

## 🔄 Active Usage

These commands are called by:
- `scripts/geo/operations/update.py` - For updating existing geographic data
- `scripts/geo/operations/populate.py` - For populating new geographic data

## ⚠️ Important Notes

1. **Data Updates**: These commands support both initial import and updates
2. **TIGER/Line Data**: Requires annual TIGER/Line boundary files
3. **State Filtering**: Can import specific states or all states
4. **Year Support**: Supports different TIGER/Line years
5. **Existing Data**: Can update existing records or clear and recreate

## 🚀 Usage Examples

```bash
# Import all states for 2023
python manage.py import_states_enhanced --all-states --year 2023

# Import specific states
python manage.py import_states_enhanced --states "KY,IN,OH" --year 2023

# Update existing data
python manage.py import_states_enhanced --states KY --year 2023 --update-existing

# Clear existing and import fresh
python manage.py import_states_enhanced --states KY --year 2023 --clear-existing
```

## 📊 Data Sources

- **TIGER/Line**: U.S. Census Bureau boundary files
- **Years Available**: 2020, 2021, 2022, 2023
- **Coverage**: United States and territories
- **Format**: Shapefiles (.shp)

## 🔧 Maintenance

These commands are maintained as part of the ongoing geographic data management workflow. They are not one-time scripts but active tools for keeping geographic data current.
