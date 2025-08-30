#!/usr/bin/env python3

import requests
import json

def test_duckduckgo_api():
    print("=== TESTING DUCKDUCKGO API DIRECTLY ===")
    
    # Test with a known organization first
    print("--- Testing with known organization: 'American Red Cross' ---")
    try:
        search_url = "https://api.duckduckgo.com/"
        params = {
            'q': 'American Red Cross',
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        print(f"Response status: {response.status_code}")
        print(f"Abstract: {data.get('Abstract', 'None')}")
        print(f"Results count: {len(data.get('Results', []))}")
        
        if data.get('Results'):
            for i, result in enumerate(data['Results'][:2]):
                print(f"  Result {i+1}: {result.get('Text', 'No text')}")
                print(f"    URL: {result.get('FirstURL', 'No URL')}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Now test with Red Bird Mission using different approaches
    print("\n--- Testing Red Bird Mission with different approaches ---")
    
    search_terms = [
        'Red Bird Mission',
        'Red Bird Mission Kentucky',
        'Red Bird Mission Beverly',
        'Red Bird Mission KY',
        'Red Bird Mission organization'
    ]
    
    for search_term in search_terms:
        print(f"\n--- Testing: {search_term} ---")
        
        try:
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': search_term,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            print(f"Response status: {response.status_code}")
            print(f"Abstract: {data.get('Abstract', 'None')}")
            print(f"Results count: {len(data.get('Results', []))}")
            
            if data.get('Results'):
                for i, result in enumerate(data['Results'][:2]):
                    print(f"  Result {i+1}: {result.get('Text', 'No text')}")
                    print(f"    URL: {result.get('FirstURL', 'No URL')}")
            
            if data.get('AbstractText'):
                print(f"AbstractText: {data['AbstractText']}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    test_duckduckgo_api()
