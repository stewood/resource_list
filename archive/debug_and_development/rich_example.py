#!/usr/bin/env python3
"""
Simple example of using Rich for JSON formatting in your own code.
"""

import json
from rich import print as rprint
from rich.json import JSON
from rich.console import Console
from rich.panel import Panel

# Your data
data = {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com",
    "skills": ["Python", "JavaScript", "SQL"],
    "active": True,
    "profile": {
        "location": "New York",
        "experience": 5,
        "certifications": ["AWS", "Docker"]
    }
}

def main():
    print("🎨 Rich JSON Examples")
    print("=" * 50)
    
    # Method 1: Simple rich.print
    print("\n1️⃣ Simple rich.print:")
    rprint(JSON.from_data(data))
    
    # Method 2: With console for more control
    print("\n2️⃣ With Console:")
    console = Console()
    console.print(JSON.from_data(data))
    
    # Method 3: In a panel
    print("\n3️⃣ In a Panel:")
    panel = Panel(JSON.from_data(data), title="User Profile", border_style="blue")
    console.print(panel)
    
    # Method 4: Custom styling
    print("\n4️⃣ With custom styling:")
    console.print(JSON.from_data(data), style="bold green")
    
    # Method 5: Just the JSON string with rich.print
    print("\n5️⃣ JSON string with rich.print:")
    json_str = json.dumps(data, indent=2)
    rprint(json_str)

if __name__ == "__main__":
    main()
