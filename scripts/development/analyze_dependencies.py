#!/usr/bin/env python3
"""
Dependency Analysis Script

This script analyzes the dependencies between Python files in the project
to identify circular dependencies and understand the import structure.

Usage:
    python scripts/analyze_dependencies.py
"""

import os
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple

def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environment and cache directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def extract_imports(file_path: str) -> List[str]:
    """Extract all import statements from a Python file."""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all import statements
        import_patterns = [
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def normalize_import_path(import_path: str, current_file: str) -> str:
    """Convert relative imports to absolute paths."""
    if import_path.startswith('.'):
        # Relative import
        current_dir = os.path.dirname(current_file)
        parts = import_path.split('.')
        
        # Remove leading dots
        while parts and parts[0] == '':
            parts.pop(0)
        
        if parts:
            # Navigate up directories based on number of dots
            for _ in range(len(import_path) - len(import_path.lstrip('.'))):
                current_dir = os.path.dirname(current_dir)
            
            # Build the path
            result_path = os.path.join(current_dir, *parts)
            return result_path
    
    return import_path

def build_dependency_graph(python_files: List[str]) -> Dict[str, Set[str]]:
    """Build a dependency graph from Python files."""
    graph = defaultdict(set)
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        
        for import_path in imports:
            # Try to find the actual file
            normalized_path = normalize_import_path(import_path, file_path)
            
            # Look for the imported module
            for potential_file in python_files:
                if normalized_path in potential_file or import_path in potential_file:
                    graph[file_path].add(potential_file)
                    break
    
    return graph

def find_circular_dependencies(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find circular dependencies using DFS."""
    def dfs(node: str, path: List[str], visited: Set[str], rec_stack: Set[str]) -> List[List[str]]:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            return [path[cycle_start:] + [node]]
        
        if node in visited:
            return []
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        cycles = []
        for neighbor in graph.get(node, []):
            cycles.extend(dfs(neighbor, path, visited, rec_stack))
        
        path.pop()
        rec_stack.remove(node)
        return cycles
    
    visited = set()
    all_cycles = []
    
    for node in graph:
        if node not in visited:
            cycles = dfs(node, [], visited, set())
            all_cycles.extend(cycles)
    
    return all_cycles

def analyze_large_files(python_files: List[str]) -> List[Tuple[str, int]]:
    """Analyze the largest Python files."""
    file_sizes = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                file_sizes.append((file_path, lines))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return sorted(file_sizes, key=lambda x: x[1], reverse=True)

def main():
    """Main analysis function."""
    print("🔍 Analyzing Python file dependencies...")
    print("=" * 60)
    
    # Find all Python files
    python_files = find_python_files('.')
    print(f"Found {len(python_files)} Python files")
    
    # Analyze large files
    print("\n📊 Largest Python files:")
    print("-" * 40)
    large_files = analyze_large_files(python_files)
    
    for file_path, line_count in large_files[:10]:
        relative_path = os.path.relpath(file_path, '.')
        print(f"{relative_path:<50} {line_count:>6} lines")
    
    # Build dependency graph
    print("\n🔗 Building dependency graph...")
    graph = build_dependency_graph(python_files)
    
    # Find circular dependencies
    print("\n🔄 Checking for circular dependencies...")
    cycles = find_circular_dependencies(graph)
    
    if cycles:
        print(f"Found {len(cycles)} circular dependency cycles:")
        for i, cycle in enumerate(cycles, 1):
            print(f"\nCycle {i}:")
            for file_path in cycle:
                relative_path = os.path.relpath(file_path, '.')
                print(f"  → {relative_path}")
    else:
        print("✅ No circular dependencies found!")
    
    # Analyze specific large files
    print("\n📋 Detailed analysis of largest files:")
    print("-" * 50)
    
    large_file_paths = [f[0] for f in large_files[:5]]
    
    for file_path in large_file_paths:
        relative_path = os.path.relpath(file_path, '.')
        print(f"\n📄 {relative_path}")
        
        imports = extract_imports(file_path)
        print(f"   Imports ({len(imports)}):")
        
        # Group imports by type
        django_imports = [imp for imp in imports if imp.startswith('django')]
        local_imports = [imp for imp in imports if not imp.startswith(('django', 'typing', 'json', 'os', 'sys', 'pathlib', 'datetime', 'logging', 'argparse'))]
        stdlib_imports = [imp for imp in imports if imp in ['json', 'os', 'sys', 'pathlib', 'datetime', 'logging', 'argparse', 'typing']]
        
        if django_imports:
            print(f"     Django: {', '.join(django_imports[:5])}{'...' if len(django_imports) > 5 else ''}")
        if local_imports:
            print(f"     Local:  {', '.join(local_imports[:5])}{'...' if len(local_imports) > 5 else ''}")
        if stdlib_imports:
            print(f"     Stdlib: {', '.join(stdlib_imports)}")
    
    # Generate dependency report
    print("\n📈 Dependency Statistics:")
    print("-" * 30)
    
    total_dependencies = sum(len(deps) for deps in graph.values())
    avg_dependencies = total_dependencies / len(graph) if graph else 0
    
    print(f"Total files: {len(python_files)}")
    print(f"Total dependencies: {total_dependencies}")
    print(f"Average dependencies per file: {avg_dependencies:.1f}")
    print(f"Files with dependencies: {len(graph)}")
    print(f"Circular dependency cycles: {len(cycles)}")
    
    # Save detailed report
    report_file = "docs/DEPENDENCY_ANALYSIS_REPORT.md"
    print(f"\n💾 Saving detailed report to {report_file}...")
    
    with open(report_file, 'w') as f:
        f.write("# Dependency Analysis Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total Python files: {len(python_files)}\n")
        f.write(f"- Total dependencies: {total_dependencies}\n")
        f.write(f"- Average dependencies per file: {avg_dependencies:.1f}\n")
        f.write(f"- Circular dependency cycles: {len(cycles)}\n\n")
        
        f.write("## Largest Files\n\n")
        for file_path, line_count in large_files[:10]:
            relative_path = os.path.relpath(file_path, '.')
            f.write(f"- `{relative_path}`: {line_count} lines\n")
        
        if cycles:
            f.write("\n## Circular Dependencies\n\n")
            for i, cycle in enumerate(cycles, 1):
                f.write(f"### Cycle {i}\n\n")
                for file_path in cycle:
                    relative_path = os.path.relpath(file_path, '.')
                    f.write(f"- `{relative_path}`\n")
                f.write("\n")
        
        f.write("## Dependency Graph\n\n")
        for file_path, deps in sorted(graph.items()):
            if deps:  # Only show files with dependencies
                relative_path = os.path.relpath(file_path, '.')
                f.write(f"### {relative_path}\n\n")
                for dep in sorted(deps):
                    dep_relative = os.path.relpath(dep, '.')
                    f.write(f"- `{dep_relative}`\n")
                f.write("\n")
    
    print("✅ Analysis complete!")

if __name__ == "__main__":
    from datetime import datetime
    main()
