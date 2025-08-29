#!/usr/bin/env python3
"""Test FIPS code extraction."""

import re

# State FIPS code mapping
STATE_FIPS_CODES = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
    'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13',
    'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19',
    'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
    'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29',
    'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45',
    'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50',
    'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56',
    'DC': '11', 'AS': '60', 'GU': '66', 'MP': '69', 'PR': '72', 'VI': '78'
}

def extract_fips_codes(county_name):
    """Extract state and county FIPS codes from county name."""
    print(f"Processing: {county_name}")
    
    # Extract state from county name (e.g., "Abbs Valley, VA" -> "VA")
    state_match = re.search(r',\s*([A-Z]{2})$', county_name)
    if not state_match:
        print("  No state match found")
        return {}
    
    state_code = state_match.group(1)
    print(f"  State code: {state_code}")
    
    state_fips = STATE_FIPS_CODES.get(state_code)
    if not state_fips:
        print(f"  No FIPS code found for state: {state_code}")
        return {}
    
    print(f"  State FIPS: {state_fips}")
    
    # For now, we'll create a placeholder county FIPS code
    county_name_clean = county_name.split(',')[0].strip()
    county_fips = str(hash(county_name_clean) % 900 + 100)  # 3-digit number
    print(f"  County FIPS: {county_fips}")
    
    result = {
        "state_fips": state_fips,
        "county_fips": county_fips,
        "state_code": state_code,
        "county_name": county_name_clean
    }
    
    print(f"  Result: {result}")
    return result

# Test with sample data
test_names = [
    "Abbs Valley, VA",
    "Aberdeen, IN", 
    "Aberdeen, OH",
    "Abingdon, IL",
    "Abingdon, VA"
]

print("Testing FIPS code extraction:")
print("=" * 40)

for name in test_names:
    result = extract_fips_codes(name)
    print()
