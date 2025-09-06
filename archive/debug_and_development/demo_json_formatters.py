#!/usr/bin/env python3
"""
Demonstration of different JSON formatting utilities in Python.
"""

import json
import subprocess
import sys

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
        }
    ]
}


def demo_standard_json():
    """Standard Python json module."""
    print("1️⃣ Standard Python json module:")
    print("-" * 50)
    print(json.dumps(sample_data, indent=2))
    print()


def demo_rich_library():
    """Rich library (if available)."""
    print("2️⃣ Rich library:")
    print("-" * 50)
    try:
        from rich import print as rprint
        from rich.json import JSON
        rprint(JSON.from_data(sample_data))
    except ImportError:
        print("❌ Rich library not installed. Install with: pip install rich")
    print()


def demo_colorama():
    """Colorama library (if available)."""
    print("3️⃣ Colorama library:")
    print("-" * 50)
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
        
        def colorize_json(data):
            json_str = json.dumps(data, indent=2)
            json_str = json_str.replace('"', f'{Fore.CYAN}"{Style.RESET_ALL}')
            json_str = json_str.replace(':', f'{Fore.WHITE}:{Style.RESET_ALL}')
            json_str = json_str.replace(',', f'{Fore.WHITE},{Style.RESET_ALL}')
            json_str = json_str.replace('{', f'{Fore.YELLOW}{{{Style.RESET_ALL}')
            json_str = json_str.replace('}', f'{Fore.YELLOW}}}{Style.RESET_ALL}')
            json_str = json_str.replace('[', f'{Fore.MAGENTA}[{Style.RESET_ALL}')
            json_str = json_str.replace(']', f'{Fore.MAGENTA}]{Style.RESET_ALL}')
            json_str = json_str.replace('true', f'{Fore.GREEN}true{Style.RESET_ALL}')
            json_str = json_str.replace('false', f'{Fore.RED}false{Style.RESET_ALL}')
            json_str = json_str.replace('null', f'{Fore.BLACK}null{Style.RESET_ALL}')
            return json_str
        
        print(colorize_json(sample_data))
    except ImportError:
        print("❌ Colorama library not installed. Install with: pip install colorama")
    print()


def demo_pygments():
    """Pygments library (if available)."""
    print("4️⃣ Pygments library:")
    print("-" * 50)
    try:
        from pygments import highlight
        from pygments.lexers import JsonLexer
        from pygments.formatters import TerminalFormatter
        
        json_str = json.dumps(sample_data, indent=2)
        highlighted = highlight(json_str, JsonLexer(), TerminalFormatter())
        print(highlighted)
    except ImportError:
        print("❌ Pygments library not installed. Install with: pip install pygments")
    print()


def demo_jq():
    """jq command-line tool (if available)."""
    print("5️⃣ jq command-line tool:")
    print("-" * 50)
    try:
        json_str = json.dumps(sample_data)
        result = subprocess.run(['jq', '.'], input=json_str, text=True, capture_output=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("❌ jq command failed or not found")
    except FileNotFoundError:
        print("❌ jq command not found. Install jq for your system")
    print()


def demo_custom_formatter():
    """Our custom JSON formatter."""
    print("6️⃣ Custom JSON Formatter (our implementation):")
    print("-" * 50)
    try:
        from json_formatter import print_pretty_json
        print_pretty_json(sample_data, clean=True, use_colors=True)
    except ImportError:
        print("❌ Custom formatter not available")
    print()


def demo_termcolor():
    """termcolor library (if available)."""
    print("7️⃣ termcolor library:")
    print("-" * 50)
    try:
        from termcolor import colored
        
        def pretty_json(data):
            json_str = json.dumps(data, indent=2)
            lines = json_str.split('\n')
            colored_lines = []
            for line in lines:
                if '"' in line:
                    line = colored(line, 'cyan')
                elif '{' in line or '}' in line:
                    line = colored(line, 'yellow')
                elif '[' in line or ']' in line:
                    line = colored(line, 'magenta')
                colored_lines.append(line)
            return '\n'.join(colored_lines)
        
        print(pretty_json(sample_data))
    except ImportError:
        print("❌ termcolor library not installed. Install with: pip install termcolor")
    print()


def main():
    """Run all demonstrations."""
    print("🎨 JSON Formatting Utilities Demo")
    print("=" * 80)
    print()
    
    demo_standard_json()
    demo_rich_library()
    demo_colorama()
    demo_pygments()
    demo_jq()
    demo_custom_formatter()
    demo_termcolor()
    
    print("📋 Summary of available utilities:")
    print("-" * 50)
    print("✅ Standard json module - Always available")
    print("✅ Custom formatter - Our implementation with cleaning")
    
    # Check which libraries are available
    libraries = [
        ("rich", "pip install rich"),
        ("colorama", "pip install colorama"),
        ("pygments", "pip install pygments"),
        ("termcolor", "pip install termcolor")
    ]
    
    for lib, install_cmd in libraries:
        try:
            __import__(lib)
            print(f"✅ {lib} - Available")
        except ImportError:
            print(f"❌ {lib} - Install with: {install_cmd}")
    
    # Check jq
    try:
        subprocess.run(['jq', '--version'], capture_output=True, check=True)
        print("✅ jq - Available")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ jq - Install for your system")


if __name__ == "__main__":
    main()
