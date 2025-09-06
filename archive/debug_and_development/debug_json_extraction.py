#!/usr/bin/env python3
"""
Debug script to test JSON extraction from messy content.
"""

import json
import re
from rich import print as rprint
from rich.json import JSON
from rich.panel import Panel
from rich.console import Console

# Sample messy content (similar to what we're getting from cursor-agent)
messy_content = '''[
  {
    "title": "How To Code In Python - Learn by Doing",
    "url": "//duckduckgo.com/l/?uddg=https%3A%2F%2Fduckduckgo.com%2Fy.js%3Fad_domain%3Dcodecademy.com%26ad_provider%3Dbingv7aa%26ad_type%3Dtxad%26click_metadata%3Dn86VwlECunAIKqaY9KoVBOyMtnoVSElg0PKfkqpstwSfEr_u2LMM5hijhl72R01s3JxYVp6HPqiJkwuDNzTCCGykAX3D2D8wUKUxsIptMERy7Pj8YdaiycdmhZYLeRX2.38pjC2GJBHia52nr%252DeNnEw%26rut%3D70863260e9e8f24536936c8a591c11d7449493f19ede5875a5d6da7c15755865%26u3%3Dhttps%253A%252F%252Fwww.bing.com%252Faclick%253Fld%253De8fR0kcWH5YKsul8ZoGElyLzVUCUwfqs_r0Cj1Pz%252DMHhVNNwAk%252DKZ0G_tnF5Ou%252D0POUEvbufFmdXxu9xY3WYQCVGMrVpC6hmX_v4wg6IXgiUWRq1YUbPHeRKKUZfbqaHK_hiLczBjUkBDx84O1bpkac7D6ixzMY8t348zI_%252DySp4Kp2pdh3cdUXipqrIRErdcXnCs5ew%2526u%253DaHR0cHMlM2ElMmYlMmZ3d3cuY29kZWNhZGVteS5jb20lMmZwYWdlcyUyZmxlYXJuLXB5dGhvbi13aXRoLXBybyUzZnV0bV9pZCUzZHRfa3dkLTc4NzUyOTE3ODkwNTM3JTNhbG9jLTQxMjYlM2FhZ18xMjYwMDQwOTQ3MzAzMjE2JTNhY3BfMzcwMzE0NTA4JTNhbl9zJTNhZF9jJTI2bXNjbGtpZCUzZGVlYjAyYWNlMjhlYzEyYmU1NDI5NDI3N2UzZDMwNGIwJTI2dXRtX3NvdXJjZSUzZGJpbmclMjZ1dG1fbWVkaXVtJTNkY3BjJTI2dXRtX2NhbXBhaWduJTNkVVMlMjUyMC0lMjUyMEV4YWN0JTI2dXRtX3Rlcm0lM2Rob3clMjUyMHRvJTI1MjBjb2RlJTI1MjBpbiUyNTIwcHl0aG9uJTI2dXRtX2NvbnRlbnQlM2RweXRob24%2526rlid%253Deeb02ace28ec12be54294277e3d304b0%26vqd%3D4%2D49271149960610998821700294480151270637%26iurl%3D%257B1%257DIG%253D6F7E83DF5E854AE2AC5223F7FF21AC10%2526CID%253D12C7CA209CE06CDF2B44DC7D9D066D7E%2526ID%253DDevEx%252C5045.1&rut=c5bf0724dbda034759be5365987bab0b4b0536d73a89a333153901878176092c",
    "description": "Learn key takeaway skills of Python and earn a certificate of completion. Take your skills to a new level and join millions of users that have learned Python."
  }
]'''

def extract_json_from_messy_content(content: str):
    """Extract JSON from messy content that may contain ANSI codes and other artifacts."""
    
    # Remove ANSI color codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_content = ansi_escape.sub('', content)
    
    print("Original content length:", len(content))
    print("Clean content length:", len(clean_content))
    print("First 200 chars of clean content:")
    print(repr(clean_content[:200]))
    print()
    
    # Try different JSON extraction strategies
    strategies = [
        # Strategy 1: Try to parse the entire content
        ("Entire content", lambda: json.loads(clean_content)),
        
        # Strategy 2: Find JSON array
        ("JSON array", lambda: json.loads(clean_content[clean_content.find('['):clean_content.rfind(']') + 1]) if clean_content.find('[') != -1 else None),
        
        # Strategy 3: Find JSON object
        ("JSON object", lambda: json.loads(clean_content[clean_content.find('{'):clean_content.rfind('}') + 1]) if clean_content.find('{') != -1 else None),
    ]
    
    for name, strategy in strategies:
        try:
            result = strategy()
            if result is not None:
                print(f"✅ {name} strategy succeeded!")
                return result
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"❌ {name} strategy failed: {e}")
    
    return None

def main():
    console = Console()
    
    print("🔍 Testing JSON extraction from messy content")
    print("=" * 60)
    
    # Test the extraction
    json_data = extract_json_from_messy_content(messy_content)
    
    if json_data is not None:
        print("\n🎉 JSON extraction successful!")
        
        # Display with Rich
        json_panel = Panel(
            JSON.from_data(json_data),
            title="📝 Extracted JSON",
            border_style="green"
        )
        console.print(json_panel)
    else:
        print("\n❌ JSON extraction failed!")
        
        # Show the content as text
        text_panel = Panel(
            messy_content[:500] + "..." if len(messy_content) > 500 else messy_content,
            title="📝 Raw Content",
            border_style="red"
        )
        console.print(text_panel)

if __name__ == "__main__":
    main()
