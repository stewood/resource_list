#!/usr/bin/env python3
"""
Demonstration of using the Rich library for beautiful JSON formatting.
"""

import json
from typing import Any, Dict, List

# Sample data with messy URLs and descriptions
sample_data = {
    "search_query": "Python programming",
    "results_found": 3,
    "top_results": [
        {
            "title": "Python Tutorial",
            "url": "//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.python.org%2F&rut=18487d848236137de5e8e5dfe7ab3c176d5e3018794e70e1dba2ea9b1e7be8b6",
            "description": " \n                      \n                   \n                          Welcome to Python.org\n      \n\n                    \n\n                    \n                      \n                        \n                          \n  \n                              \n                            \n            \n                          \n                            www.python.org\n                          \n                          \n      \n                      \n                    \n\n                    \n                    \n                        Python is a versatile and easy-to-learn programming language that lets you work quickly and integrate systems more effectively. Learn Python basics, download the latest version, access documentation, find jobs, events, success stories and more on the official website.\n                      \n                    \n\n                   \n                  Python is a versatile and easy-to-learn programming language that lets you work quickly and integrate systems more effectively. Learn Python basics, download the latest version, access documentation, find jobs, events, success stories and more on the official website."
        },
        {
            "title": "Learn Python",
            "url": "https://www.codecademy.com/learn/learn-python-3?utm_source=google&utm_medium=cpc&utm_campaign=python&gclid=123456789",
            "snippet": "Learn Python programming with interactive lessons and projects."
        },
        {
            "title": "Python Documentation",
            "url": "https://docs.python.org/3/",
            "snippet": "Official Python documentation with tutorials and reference materials.",
            "features": ["tutorials", "reference", "library", "extending"],
            "active": True,
            "rating": 4.8
        }
    ],
    "metadata": {
        "search_time": "2024-01-15T10:30:00Z",
        "total_results": 1500000,
        "page": 1,
        "per_page": 10
    }
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
        
        # Method 3: With background
        print("\n3️⃣ With background:")
        console.print(JSON.from_data(sample_data), style="on dark_blue")
        
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
        
        # Method 1: JSON in a panel
        print("\n1️⃣ JSON in a panel:")
        json_obj = JSON.from_data(sample_data)
        panel = Panel(json_obj, title="Search Results", border_style="green")
        console.print(panel)
        
        # Method 2: Multiple panels
        print("\n2️⃣ Multiple panels:")
        for i, result in enumerate(sample_data["top_results"], 1):
            result_json = JSON.from_data(result)
            panel = Panel(
                result_json, 
                title=f"Result {i}: {result['title']}", 
                border_style="blue"
            )
            console.print(panel)
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def demo_rich_table():
    """Rich Table for structured data."""
    try:
        from rich.console import Console
        from rich.table import Table
        
        print("\n🎨 Rich Table - Structured Display")
        print("=" * 60)
        
        console = Console()
        
        # Create a table for the search results
        table = Table(title="Search Results")
        table.add_column("Title", style="cyan", no_wrap=True)
        table.add_column("URL", style="magenta")
        table.add_column("Snippet", style="green")
        table.add_column("Features", style="yellow")
        
        for result in sample_data["top_results"]:
            features = result.get("features", [])
            features_str = ", ".join(features) if features else "N/A"
            
            # Truncate long text
            title = result["title"][:30] + "..." if len(result["title"]) > 30 else result["title"]
            snippet = result.get("snippet", "")[:50] + "..." if len(result.get("snippet", "")) > 50 else result.get("snippet", "")
            
            table.add_row(title, result["url"], snippet, features_str)
        
        console.print(table)
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def demo_rich_tree():
    """Rich Tree for hierarchical data."""
    try:
        from rich.console import Console
        from rich.tree import Tree
        
        print("\n🎨 Rich Tree - Hierarchical Display")
        print("=" * 60)
        
        console = Console()
        
        # Create a tree structure
        tree = Tree("🔍 Search Results", style="bold blue")
        
        # Add metadata
        metadata_branch = tree.add("📊 Metadata", style="yellow")
        for key, value in sample_data["metadata"].items():
            metadata_branch.add(f"{key}: {value}", style="dim")
        
        # Add results
        results_branch = tree.add("📋 Results", style="green")
        for i, result in enumerate(sample_data["top_results"], 1):
            result_branch = results_branch.add(f"Result {i}: {result['title']}", style="cyan")
            result_branch.add(f"URL: {result['url']}", style="dim")
            if "snippet" in result:
                result_branch.add(f"Snippet: {result['snippet'][:100]}...", style="dim")
            if "features" in result:
                features_branch = result_branch.add("Features", style="magenta")
                for feature in result["features"]:
                    features_branch.add(f"• {feature}", style="dim")
        
        console.print(tree)
        
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


def demo_rich_markdown():
    """Rich Markdown for documentation-style display."""
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        
        print("\n🎨 Rich Markdown - Documentation Style")
        print("=" * 60)
        
        console = Console()
        
        # Create markdown content
        markdown_content = f"""
# Search Results

**Query:** {sample_data['search_query']}  
**Results Found:** {sample_data['results_found']}  
**Total Results:** {sample_data['metadata']['total_results']:,}

## Top Results

"""
        
        for i, result in enumerate(sample_data["top_results"], 1):
            markdown_content += f"""
### {i}. {result['title']}

- **URL:** {result['url']}
- **Snippet:** {result.get('snippet', 'No snippet available')}
"""
            if "features" in result:
                markdown_content += f"- **Features:** {', '.join(result['features'])}\n"
            if "rating" in result:
                markdown_content += f"- **Rating:** {result['rating']}/5\n"
        
        markdown = Markdown(markdown_content)
        console.print(markdown)
        
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
        return False
    return True


def main():
    """Run all Rich demonstrations."""
    print("🚀 Rich Library JSON Formatting Demo")
    print("=" * 80)
    
    # Check if rich is installed
    try:
        import rich
        print(f"✅ Rich library version: {rich.__version__}")
    except ImportError:
        print("❌ Rich library not installed!")
        print("Install with: pip install rich")
        return
    
    # Run all demos
    demos = [
        demo_rich_basic,
        demo_rich_console,
        demo_rich_panel,
        demo_rich_table,
        demo_rich_tree,
        demo_rich_syntax,
        demo_rich_markdown
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
