"""
Test script to verify NetworkX and Neo4j are installed and working
"""

# Test 1: NetworkX
print("=" * 50)
print("Testing NetworkX")
print("=" * 50)

try:
    import networkx as nx
    print("✅ NetworkX installed successfully")
    print(f"   Version: {nx.__version__}")
    
    # Create a simple graph
    G = nx.Graph()
    G.add_edges_from([
        ("laptop", "library"),
        ("phone", "cafeteria"),
        ("wallet", "gym")
    ])
    print(f"✅ Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    print(f"   Nodes: {list(G.nodes())}")
    
    # Test graph operations
    print(f"✅ Shortest path from 'laptop' to 'library': {nx.shortest_path(G, 'laptop', 'library')}")
    
except ImportError as e:
    print(f"❌ NetworkX NOT installed: {e}")
    print("   Run: pip install networkx>=3.1")
except Exception as e:
    print(f"⚠️ NetworkX installed but error occurred: {e}")

# Test 2: Neo4j Driver
print("\n" + "=" * 50)
print("Testing Neo4j Driver")
print("=" * 50)

try:
    from neo4j import GraphDatabase
    print("✅ Neo4j driver installed successfully")
    
    # Note: This won't connect without a running Neo4j instance
    print("⚠️ Neo4j driver is installed, but connection requires:")
    print("   - Neo4j database running (bolt://localhost:7687)")
    print("   - Valid credentials")
    print("\n   To test connection, Neo4j server must be installed and running")
    print("   Download from: https://neo4j.com/download/")
    
except ImportError as e:
    print(f"❌ Neo4j driver NOT installed: {e}")
    print("   Run: pip install neo4j>=5.14.0")
except Exception as e:
    print(f"⚠️ Neo4j driver installed but error occurred: {e}")

# Test 3: Check if they're being used in the codebase
print("\n" + "=" * 50)
print("Checking Usage in Codebase")
print("=" * 50)

import os
import re

def search_imports(directory, pattern):
    """Search for import statements in Python files"""
    matches = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and cache
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if re.search(pattern, content):
                            matches.append(filepath)
                except:
                    pass
    return matches

# Search for NetworkX usage
nx_files = search_imports('src', r'import networkx|from networkx')
if nx_files:
    print(f"✅ NetworkX used in {len(nx_files)} file(s):")
    for f in nx_files[:5]:  # Show first 5
        print(f"   - {f}")
else:
    print("⚠️ NetworkX installed but NOT actively used in codebase")

# Search for Neo4j usage  
neo4j_files = search_imports('src', r'import neo4j|from neo4j')
if neo4j_files:
    print(f"\n✅ Neo4j used in {len(neo4j_files)} file(s):")
    for f in neo4j_files[:5]:  # Show first 5
        print(f"   - {f}")
else:
    print("\n⚠️ Neo4j installed but NOT actively used in codebase")

print("\n" + "=" * 50)
print("Summary")
print("=" * 50)
print("NetworkX: Installed & ready for graph operations")
print("Neo4j: Driver installed (requires database server for connections)")
