#!/usr/bin/env python3
"""
Simple demonstration of Rich library for JSON formatting.
"""

import json

# Sample data
sample_data = {
    "search_query": "Python programming",
    "results_found": 3,
    "top_results": [
        {
            "title": "Python Tutorial",
            "url": "https://www.python.org/",
            "description": "Python is a versatile and easy-to-learn programming language."
        },
        {
            "title": "Learn Python",
            "url": "https://www.codecademy.com/learn/learn-python-3",
            "snippet": "Learn Python programming with interactive lessons and projects."
        }
    ]
}


def demo_rich_basic():
    """Basic Rich JSON display."""
    try:
        from rich import print as rprint
        from rich.json import JSON
        
        print("🎨 Rich Library - Basic JSON Display")
        print("=" * 60)
        
        # Method 1: Using rich.print with JSON object
        print("\n1️⃣ Using rich.print with JSON object:")
        rprint(JSON.from_data(sample_data))
        
        # Method 2: Using rich.print with json.dumps
        print("\n2️⃣ Using rich.print with json.dumps:")
        rprint(json.dumps(sample_data, indent=2))
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def demo_rich_console():
    """Rich Console for more control."""
    try:
        from rich.console import Console
        from rich.json import JSON
        
        print("\n🎨 Rich Console - Advanced Display")
        print("=" * 60)
        
        console = Console()
        
        # Method 1: Direct JSON rendering
        print("\n1️⃣ Direct JSON rendering:")
        console.print(JSON.from_data(sample_data))
        
        # Method 2: With custom styling
        print("\n2️⃣ With custom styling:")
        console.print(JSON.from_data(sample_data), style="bold blue")
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def demo_rich_panel():
    """Rich Panel for contained display."""
    try:
        from rich.console import Console
        from rich.json import JSON
        from rich.panel import Panel
        
        print("\n🎨 Rich Panel - Contained Display")
        print("=" * 60)
        
        console = Console()
        
        # JSON in a panel
        print("\n1️⃣ JSON in a panel:")
        json_obj = JSON.from_data(sample_data)
        panel = Panel(json_obj, title="Search Results", border_style="green")
        console.print(panel)
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def demo_rich_syntax():
    """Rich Syntax highlighting for JSON."""
    try:
        from rich.console import Console
        from rich.syntax import Syntax
        
        print("\n🎨 Rich Syntax - JSON Highlighting")
        print("=" * 60)
        
        console = Console()
        
        # Convert to JSON string
        json_str = json.dumps(sample_data, indent=2)
        
        # Create syntax object
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        
        console.print(syntax)
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def main():
    """Run Rich demonstrations."""
    print("🚀 Rich Library JSON Formatting Demo")
    print("=" * 80)
    
    # Check if rich is installed
    try:
        import rich
        print("✅ Rich library is installed")
    except ImportError:
        print("❌ Rich library not installed!")
        print("Install with: pip install rich")
        return
    
    # Run demos
    demos = [
        demo_rich_basic,
        demo_rich_console,
        demo_rich_panel,
        demo_rich_syntax
    ]
    
    for demo in demos:
        try:
            demo()
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"❌ Error in {demo.__name__}: {e}")
            print("\n" + "="*80 + "\n")
    
    print("🎉 Demo completed!")


if __name__ == "__main__":
    main()
