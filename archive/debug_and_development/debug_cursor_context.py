#!/usr/bin/env python3
"""
Debug script to test cursor-agent contexts and MCP tool availability.
This helps diagnose why MCP tools work when running cursor-agent directly
but not when called as a subprocess from Django management commands.
"""

import subprocess
import os
import sys
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a command and capture output"""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print("-" * 50)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )

        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")

        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}")
        return False, "", str(e)

def test_context(name, cmd, env_vars=None):
    """Test a specific context"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING CONTEXT: {name}")
    print(f"{'='*60}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"PATH: {os.environ.get('PATH', 'Not set')[:100]}...")

    # Test environment variables
    key_vars = ['HOME', 'USER', 'SHELL', 'PATH', 'CURSOR_API_KEY']
    print("\n📋 Key Environment Variables:")
    for var in key_vars:
        value = os.environ.get(var, 'Not set')
        if 'KEY' in var or 'TOKEN' in var:
            print(f"  {var}: {'*' * len(value) if value != 'Not set' else value}")
        else:
            print(f"  {var}: {value}")

    # Modify environment if specified
    if env_vars:
        test_env = os.environ.copy()
        test_env.update(env_vars)
        print(f"\n🔧 Modified environment: {env_vars}")
    else:
        test_env = os.environ.copy()

    # Run the command
    success, stdout, stderr = run_command(cmd, f"Running {name}")

    return success, stdout, stderr

def main():
    """Main debug function"""
    print("🚀 Cursor Agent Context Debug Script")
    print("=" * 60)

    # Test 1: Direct cursor-agent status
    test_context(
        "Direct cursor-agent status",
        ["cursor-agent", "status"]
    )

    # Test 2: Direct cursor-agent MCP list
    test_context(
        "Direct cursor-agent MCP list",
        ["cursor-agent", "mcp", "list"]
    )

    # Test 3: Direct cursor-agent MCP tools
    test_context(
        "Direct cursor-agent MCP tools",
        ["cursor-agent", "mcp", "list-tools", "mcp-search"]
    )

    # Test 4: Subprocess cursor-agent status (simulating Django context)
    test_context(
        "Subprocess cursor-agent status",
        ["cursor-agent", "status"]
    )

    # Test 5: Subprocess with explicit environment
    test_context(
        "Subprocess with explicit env",
        ["cursor-agent", "status"],
        {"PYTHONPATH": os.getcwd()}
    )

    # Test 6: Simple MCP tool test
    test_context(
        "Simple web_search test",
        ["cursor-agent", "--force", "--print", "-f", "--model", "auto", "Use web_search to find 'test query' and return results"]
    )

    # Test 7: Simple MCP tool test without model flag
    test_context(
        "Simple web_search test (no model flag)",
        ["cursor-agent", "--force", "--print", "-f", "Use web_search to find 'test query' and return results"]
    )

    # Test 8: Hardcoded website discovery prompt (same as verify_cli.py)
    website_discovery_prompt = '''Find as many URLs as possible with information about this resource using chain of thought reasoning.

Resource: Battered Women's Justice Project (BWJP)
Category: Hotlines
Description: BWJP is a collective of national policy and practice centers that provides technical assistance to professionals working with domestic violence cases. They offer resources, training, consultations, and research at the intersection of gender-based violence and legal systems. BWJP recently merged with Global Rights for Women to expand their global impact.

Location: St. Paul, MN

Think through this step by step:

1. First, consider what type of organization this is and what search terms would be most effective
2. Think about where such organizations typically have online presence
3. Consider both official and unofficial sources that might mention this resource
4. Plan your search strategy to cover multiple angles

Search for:
- Official organization website
- Social media profiles (Facebook, Twitter, LinkedIn, Instagram)
- Directory listings (Google Business, Yelp, Yellow Pages)
- News articles or press coverage
- Government or nonprofit database listings
- Service provider directories
- Any other websites mentioning this resource

IMPORTANT: Follow this three-step process:
1. Use the web_search tool to search for URLs and information about this organization
2. Use pull_markdown to extract content from discovered websites
3. Use render_html only if you need to see the visual layout of complex pages

CRITICAL: Before launching any MCP tool, explain what you are about to do and why. For example:
- "I will now use web_search to search for 'Battered Women's Justice Project (BWJP) St. Paul' because this will find official and directory listings"
- "I will now use pull_markdown to extract content from [URL] because this will give me clean text to analyze"
- "I will now use render_html to view [URL] because this page may have complex formatting that needs visual inspection"

AVAILABLE MCP TOOLS:
- web_search: Search the web using DuckDuckGo (privacy-focused, no rate limits)
- pull_markdown: Convert any webpage to clean Markdown format
- render_html: Render HTML content in browser for visual inspection

Use these tools strategically - start with web search, then pull content from promising URLs.

MCP TOOLS USAGE GUIDE:
- web_search: Use for finding URLs and general information. Query format: organization name + location + "contact" or "phone" or "address"
- pull_markdown: Use for extracting readable text from websites. Best for contact pages, about pages, and service descriptions
- render_html: Use only when you need to see interactive elements, forms, or complex page layouts that markdown can't capture properly

EXAMPLE WORKFLOW:
1. "I will use web_search with query 'Battered Women's Justice Project (BWJP) St. Paul contact information' to find official contact details"
2. "Based on search results, I will use pull_markdown on the official website to extract contact information"
3. "If the website has complex forms, I will use render_html to see the full contact page layout"

Use chain of thought to explain your search process, then provide your findings in this exact JSON format:

{
  "search_strategy": "Brief description of your search approach",
  "urls_found": [
    {
      "url": "https://example.com",
      "type": "official_website|social_media|directory|news|other",
      "description": "Brief description of what this URL contains",
      "reason": "Why this URL is relevant and useful for verification"
    }
  ],
  "total_urls": 0,
  "search_notes": "Any additional notes about your search process"
}

IMPORTANT: Complete the JSON structure above and then print <|END|> to signal completion.'''

    test_context(
        "Hardcoded website discovery prompt",
        ["cursor-agent", "--force", "--print", "-f", "--model", "auto", website_discovery_prompt]
    )

    # Test 9: Check MCP configuration files
    print(f"\n{'='*60}")
    print("🔧 MCP Configuration Check")
    print(f"{'='*60}")

    config_paths = [
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".cursor" / "mcprc",
        Path.cwd() / ".cursor" / "mcp.json",
        Path.cwd() / ".cursor" / "mcprc"
    ]

    for config_path in config_paths:
        exists = config_path.exists()
        print(f"  {config_path}: {'✅' if exists else '❌'} {'Found' if exists else 'Not found'}")
        if exists:
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                    print(f"    Content preview: {content[:200]}...")
            except Exception as e:
                print(f"    Error reading: {e}")

    print(f"\n{'='*60}")
    print("🏁 Debug Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
