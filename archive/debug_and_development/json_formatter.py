#!/usr/bin/env python3
"""
Enhanced JSON formatter with colorization and cleaning utilities.
"""

import json
import re
from typing import Any, Dict, List, Union
from urllib.parse import urlparse, parse_qs, urlunparse, unquote


class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


class JSONFormatter:
    """Enhanced JSON formatter with colorization and cleaning."""
    
    def __init__(self, use_colors: bool = None):
        # Auto-detect color support if not specified
        if use_colors is None:
            self.use_colors = self._supports_color()
        else:
            self.use_colors = use_colors
    
    def _supports_color(self) -> bool:
        """Check if the terminal supports colors."""
        import os
        import sys
        
        # Check if we're in a TTY
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check environment variables
        if os.environ.get('NO_COLOR'):
            return False
        
        # Check if TERM supports colors
        term = os.environ.get('TERM', '').lower()
        if term in ['dumb', 'unknown']:
            return False
        
        # Check for common color-supporting terminals
        color_terms = ['xterm', 'xterm-256color', 'screen', 'tmux', 'linux', 'cygwin']
        if any(term.startswith(t) for t in color_terms):
            return True
        
        # Check for Windows
        if os.name == 'nt':
            try:
                import colorama
                return True
            except ImportError:
                return False
        
        return True
    
    def clean_url(self, url: str) -> str:
        """Clean up URLs by removing tracking parameters."""
        if not url:
            return url
            
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        url = ansi_escape.sub('', url)
        
        # Handle DuckDuckGo redirect URLs
        if 'duckduckgo.com/l/?uddg=' in url:
            try:
                start = url.find('uddg=') + 5
                end = url.find('&', start)
                if end == -1:
                    end = len(url)
                encoded_url = url[start:end]
                url = unquote(encoded_url)
            except:
                pass
        
        # Parse and clean the URL
        try:
            parsed = urlparse(url)
            # Remove common tracking parameters
            query_params = parse_qs(parsed.query)
            clean_params = {}
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 
                'utm_content', 'fbclid', 'gclid', 'msclkid', 'ref'
            }
            
            for key, value in query_params.items():
                if key.lower() not in tracking_params:
                    clean_params[key] = value[0] if len(value) == 1 else value
            
            # Rebuild URL
            clean_query = '&'.join([f"{k}={v}" for k, v in clean_params.items()])
            clean_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, 
                parsed.params, clean_query, parsed.fragment
            ))
            return clean_url
        except:
            return url
    
    def clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace and formatting artifacts."""
        if not text:
            return text
            
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove common artifacts
        text = re.sub(r'\n\s*\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def clean_json_data(self, data: Any) -> Any:
        """Recursively clean JSON data."""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if key in ['url', 'link', 'href']:
                    cleaned[key] = self.clean_url(str(value))
                elif key in ['description', 'snippet', 'summary', 'text', 'content']:
                    cleaned[key] = self.clean_text(str(value))
                elif isinstance(value, (dict, list)):
                    cleaned[key] = self.clean_json_data(value)
                else:
                    cleaned[key] = value
            return cleaned
        elif isinstance(data, list):
            return [self.clean_json_data(item) for item in data]
        else:
            return data
    
    def colorize_json(self, json_str: str) -> str:
        """Add colors to JSON string for better readability."""
        if not self.use_colors:
            return json_str
        
        import re
        
        # More sophisticated colorization that doesn't break JSON structure
        lines = json_str.split('\n')
        colored_lines = []
        
        for line in lines:
            # Colorize structural elements first
            line = re.sub(r'(\{)', f'{Colors.YELLOW}\\1{Colors.RESET}', line)
            line = re.sub(r'(\})', f'{Colors.YELLOW}\\1{Colors.RESET}', line)
            line = re.sub(r'(\[)', f'{Colors.MAGENTA}\\1{Colors.RESET}', line)
            line = re.sub(r'(\])', f'{Colors.MAGENTA}\\1{Colors.RESET}', line)
            
            # Colorize colons and commas (but not inside strings)
            line = re.sub(r'(\s*)(:)(\s*)', f'\\1{Colors.WHITE}\\2{Colors.RESET}\\3', line)
            line = re.sub(r'(,)(\s*$)', f'{Colors.WHITE}\\1{Colors.RESET}\\2', line)
            
            # Colorize string values (quoted text)
            line = re.sub(r'("(?:[^"\\]|\\.)*")', f'{Colors.CYAN}\\1{Colors.RESET}', line)
            
            # Colorize boolean and null values
            line = re.sub(r'\b(true)\b', f'{Colors.GREEN}\\1{Colors.RESET}', line)
            line = re.sub(r'\b(false)\b', f'{Colors.RED}\\1{Colors.RESET}', line)
            line = re.sub(r'\b(null)\b', f'{Colors.GRAY}\\1{Colors.RESET}', line)
            
            # Colorize numbers
            line = re.sub(r'\b(\d+)\b', f'{Colors.BLUE}\\1{Colors.RESET}', line)
            
            colored_lines.append(line)
        
        return '\n'.join(colored_lines)
    
    def format_json(self, data: Any, indent: int = 2, clean: bool = True) -> str:
        """
        Format JSON data with optional cleaning and colorization.
        
        Args:
            data: JSON data to format
            indent: Indentation level
            clean: Whether to clean URLs and text
            
        Returns:
            Formatted JSON string
        """
        if clean:
            data = self.clean_json_data(data)
        
        json_str = json.dumps(data, indent=indent, default=str, ensure_ascii=False)
        return self.colorize_json(json_str)
    
    def print_json(self, data: Any, indent: int = 2, clean: bool = True) -> None:
        """Print formatted JSON data."""
        formatted = self.format_json(data, indent, clean)
        print(formatted)


def pretty_json(data: Any, indent: int = 2, clean: bool = True, use_colors: bool = True) -> str:
    """
    Convenience function for pretty JSON formatting.
    
    Args:
        data: JSON data to format
        indent: Indentation level
        clean: Whether to clean URLs and text
        use_colors: Whether to use colors
        
    Returns:
        Formatted JSON string
    """
    formatter = JSONFormatter(use_colors=use_colors)
    return formatter.format_json(data, indent, clean)


def print_pretty_json(data: Any, indent: int = 2, clean: bool = True, use_colors: bool = True) -> None:
    """
    Convenience function for printing pretty JSON.
    
    Args:
        data: JSON data to format
        indent: Indentation level
        clean: Whether to clean URLs and text
        use_colors: Whether to use colors
    """
    formatter = JSONFormatter(use_colors=use_colors)
    formatter.print_json(data, indent, clean)


def test_color_support():
    """Test color support in the current terminal."""
    formatter = JSONFormatter()
    print("🔍 Color Support Test")
    print("=" * 50)
    print(f"Terminal supports colors: {formatter.use_colors}")
    print(f"TERM environment variable: {os.environ.get('TERM', 'Not set')}")
    print(f"NO_COLOR environment variable: {os.environ.get('NO_COLOR', 'Not set')}")
    print(f"stdout.isatty(): {sys.stdout.isatty()}")
    
    # Test actual color output
    print("\n🎨 Color test:")
    if formatter.use_colors:
        print(f"{Colors.RED}Red text{Colors.RESET}")
        print(f"{Colors.GREEN}Green text{Colors.RESET}")
        print(f"{Colors.BLUE}Blue text{Colors.RESET}")
        print(f"{Colors.YELLOW}Yellow text{Colors.RESET}")
        print(f"{Colors.CYAN}Cyan text{Colors.RESET}")
        print(f"{Colors.MAGENTA}Magenta text{Colors.RESET}")
    else:
        print("Colors disabled - showing raw codes:")
        print(f"{Colors.RED}Red text{Colors.RESET}")
        print(f"{Colors.GREEN}Green text{Colors.RESET}")
    print()


# Example usage
if __name__ == "__main__":
    import os
    import sys
    
    # Test color support first
    test_color_support()
    
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
    
    print("🧪 Testing JSON Formatter")
    print("=" * 80)
    
    print("\n📋 Original data:")
    print(json.dumps(sample_data, indent=2))
    
    print("\n🎨 Formatted with auto-detected colors and cleaning:")
    print_pretty_json(sample_data, clean=True, use_colors=None)  # Auto-detect
    
    print("\n📝 Formatted without colors:")
    print_pretty_json(sample_data, clean=True, use_colors=False)
