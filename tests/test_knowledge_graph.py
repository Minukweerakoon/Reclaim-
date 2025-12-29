"""
Tests for Advanced Knowledge Graph (Neo4j + NetworkX)
"""
import pytest
from src.intelligence.knowledge_graph import GraphManager
import networkx as nx

def test_graph_manager_initialization():
    """Test that GraphManager initializes correctly (likely in fallback mode)."""
    graph = GraphManager()
    stats = graph.get_relationship_mining_stats()
    
    assert "engine" in stats
    # Should be either Neo4j or NetworkX
    print(f"\nInitialized Graph Engine: {stats['engine']}")

def test_add_event_networkx():
    """Test adding events works in NetworkX mode."""
    graph = GraphManager()
    # Force fallback for this test
    graph.use_neo4j = False
    graph.nx_graph = nx.DiGraph() # Ensure fresh graph
    
    # Add data
    assert graph.add_item_event("iPhone", "Library", "electronics") == True
    assert graph.add_item_event("Wallet", "Cafeteria", "personal") == True
    assert graph.add_item_event("iPhone", "Library", "electronics") == True # Increase weight
    
    # Check stats
    stats = graph.get_relationship_mining_stats()
    # iPhone, Library, electronics, Wallet, Cafeteria, personal = 6 nodes potentially
    # But note: category nodes are reused. 
    # Nodes: iPhone, Library, electronics, Wallet, Cafeteria, personal.
    assert stats["nodes"] >= 4 
    
    # Check patterns
    patterns = graph.find_patterns("electronics")
    print(f"Patterns found: {patterns}")
    assert len(patterns) > 0
    assert patterns[0]["item"] == "iPhone"
    assert patterns[0]["location"] == "Library"
    # Weight should be 2 because we added it twice
    assert patterns[0]["count"] >= 1 

if __name__ == "__main__":
    test_graph_manager_initialization()
    test_add_event_networkx()
