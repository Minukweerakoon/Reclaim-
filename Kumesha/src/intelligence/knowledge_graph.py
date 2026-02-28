"""
Advanced Knowledge Graph Module (Neo4j + NetworkX Fallback)
Part of Research-Grade Enhancement (Novel Contribution #1)

This module implements a hybrid Knowledge Graph architecture:
1. Primary: Neo4j (for complex relationship mining and huge datasets)
2. Fallback: NetworkX (in-memory graph for offline resilience)

Research Value: Enables "Spatial-Temporal Risk Assessment" and pattern mining.
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

# Try to import NetworkX and Neo4j
try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logger = logging.getLogger(__name__)

class GraphManager:
    """
    Hybrid Knowledge Graph Manager.
    Automatically switches between Neo4j and NetworkX based on availability.
    """
    
    def __init__(self):
        """Initialize the graph manager."""
        self.use_neo4j = False
        self.driver = None
        self.nx_graph = nx.DiGraph() if nx else None
        
        # Neo4j Configuration
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        
        # Attempt Neo4j connection
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                self.driver.verify_connectivity()
                self.use_neo4j = True
                logger.info("✓ Connected to Neo4j Knowledge Graph")
                self._init_neo4j_schema()
            except Exception as e:
                logger.warning(f"⚠ Could not connect to Neo4j ({e}). Using NetworkX fallback.")
                self.use_neo4j = False
        else:
            logger.info("ℹ Neo4j driver not installed. Using NetworkX fallback.")
            
        if not self.use_neo4j and self.nx_graph is None:
            logger.error("CRITICAL: Neither Neo4j nor NetworkX is available!")
            
        # Initialize NetworkX (always available as fallback/cache)
        if self.nx_graph is not None:
            self._init_networkx_schema()
        
    def close(self):
        """Close Neo4j connection.        """
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
        
    def _init_neo4j_schema(self):
        """Initialize Neo4j constraints and indexes."""
        if not self.use_neo4j:
            return
            
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (i:Item) ON (i.category)"
        ]
        
        with self.driver.session() as session:
            for q in queries:
                session.run(q)

    def _init_networkx_schema(self):
        """Initialize NetworkX structure (if needed)."""
        # NetworkX is schema-less, but we can pre-populate static data
        pass

    def add_item_event(self, item_type: str, location: str, category: str = "unknown") -> bool:
        """
        Ingest a new item event into the Knowledge Graph.
        
        Args:
            item_type: Type of item (e.g., "phone")
            location: Place found (e.g., "library")
            category: Item category (e.g., "electronics")
        """
        day_of_week = datetime.now().strftime("%A")
        
        try:
            # 1. Update NetworkX (Always)
            if self.nx_graph is not None:
                self._add_to_networkx(item_type, location, category, day_of_week)
            
            # 2. Update Neo4j (If available)
            if self.use_neo4j:
                self._add_to_neo4j(item_type, location, category, day_of_week)
                
            return True
        except Exception as e:
            logger.error(f"Error adding event to Knowledge Graph: {e}")
            return False

    def _add_to_neo4j(self, item: str, location: str, category: str, day: str):
        """Add event to Neo4j."""
        query = """
        MERGE (c:Category {name: $category})
        MERGE (i:Item {name: $item})
        MERGE (l:Location {name: $location})
        MERGE (t:Time {day: $day})
        
        MERGE (i)-[:BELONGS_TO]->(c)
        MERGE (i)-[:FOUND_AT {confidence: 1.0}]->(l)
        MERGE (i)-[:REPORTED_ON]->(t)
        
        # Update occurrence count on the relationship
        MERGE (i)-[r:OFTEN_FOUND_IN]->(l)
        ON CREATE SET r.count = 1
        ON MATCH SET r.count = r.count + 1
        """
        with self.driver.session() as session:
            session.run(query, item=item, location=location, category=category, day=day)

    def _add_to_networkx(self, item: str, location: str, category: str, day: str):
        """Add event to NetworkX."""
        # Nodes
        self.nx_graph.add_node(item, type="Item", category=category)
        self.nx_graph.add_node(location, type="Location")
        self.nx_graph.add_node(category, type="Category")
        
        # Relationships
        self.nx_graph.add_edge(item, location, relation="FOUND_AT")
        self.nx_graph.add_edge(item, category, relation="BELONGS_TO")
        
        # Track frequency (simple weight)
        edge_key = (item, location)
        if self.nx_graph.has_edge(*edge_key):
            self.nx_graph.edges[edge_key]['weight'] = self.nx_graph.edges[edge_key].get('weight', 0) + 1
        else:
            self.nx_graph.add_edge(item, location, weight=1, relation="OFTEN_FOUND_IN")

    def find_patterns(self, item_category: str) -> List[Dict]:
        """
        Discover spatial patterns for a category.
        e.g., "Where are electronics usually found?"
        """
        if self.use_neo4j:
            return self._query_neo4j_patterns(item_category)
        elif self.nx_graph is not None:
            return self._query_networkx_patterns(item_category)
        return []

    def _query_neo4j_patterns(self, category: str) -> List[Dict]:
        """Run Cypher query for user patterns."""
        query = """
        MATCH (c:Category {name: $category})<-[:BELONGS_TO]-(i:Item)
        MATCH (i)-[r:OFTEN_FOUND_IN]->(l:Location)
        RETURN i.name as item, l.name as location, r.count as count
        ORDER BY count DESC
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, category=category)
            return [{"item": r["item"], "location": r["location"], "count": r["count"]} for r in result]

    def _query_networkx_patterns(self, category: str) -> List[Dict]:
        """Run Graph traversal for patterns."""
        results = []
        
        # Find all items in category
        items = [n for n, attr in self.nx_graph.nodes(data=True) 
                 if attr.get('type') == 'Item' and attr.get('category') == category]
        
        for item in items:
            # Find locations connected to these items
            for neighbor in self.nx_graph.neighbors(item):
                edge_data = self.nx_graph.get_edge_data(item, neighbor)
                if edge_data.get('relation') == 'OFTEN_FOUND_IN':
                    results.append({
                        "item": item,
                        "location": neighbor,
                        "count": edge_data.get('weight', 1)
                    })
        
        # Sort by count
        return sorted(results, key=lambda x: x['count'], reverse=True)[:5]

    def get_relationship_mining_stats(self) -> Dict:
        """Get stats about graph size and connectivity."""
        if self.use_neo4j:
            try:
                with self.driver.session() as session:
                    res = session.run("MATCH (n) RETURN count(n) as nodes")
                    nodes = res.single()["nodes"]
                    res = session.run("MATCH ()-[r]->() RETURN count(r) as rels")
                    rels = res.single()["rels"]
                    return {"engine": "Neo4j", "nodes": nodes, "relationships": rels}
            except Exception as e:
                logger.error(f"Error getting Neo4j stats: {e}")
                return {"engine": "Neo4j (Error)", "error": str(e)}
        else:
            if self.nx_graph is not None:
                return {
                    "engine": "NetworkX (Fallback)", 
                    "nodes": self.nx_graph.number_of_nodes(),
                    "relationships": self.nx_graph.number_of_edges()
                }
            else:
                return {"engine": "None", "nodes": 0, "relationships": 0}

    # ------------------------------------------------------------------ #
    # Spatial-Temporal Context Methods (Novel Feature #1)
    # ------------------------------------------------------------------ #
    def record_item_context(
        self, 
        item_type: str, 
        location: str, 
        time_of_day: Optional[str] = None,
        validated: bool = True
    ) -> bool:
        """
        Record a validated item's spatial-temporal context.
        This data is used to improve Bayesian plausibility scoring.
        
        Args:
            item_type: Type of item (e.g., "phone", "laptop")
            location: Where the item was found/lost
            time_of_day: Time period or specific time
            validated: Whether this was a validated (confirmed) report
            
        Returns:
            bool: True if recorded successfully
        """
        try:
            # Also update the spatial-temporal validator's learned patterns
            from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator
            stv = get_spatial_temporal_validator()
            stv.record_validated_item(item_type, location, time_of_day)
            
            # Add to graph for relationship mining
            category = self._infer_category(item_type)
            self.add_item_event(item_type, location, category)
            
            logger.info(f"Recorded spatial-temporal context: {item_type} at {location}, time={time_of_day}")
            return True
        except Exception as e:
            logger.error(f"Failed to record item context: {e}")
            return False
    
    def _infer_category(self, item_type: str) -> str:
        """Infer category from item type."""
        item_lower = item_type.lower()
        if any(x in item_lower for x in ["phone", "laptop", "tablet", "watch", "headphone", "airpod"]):
            return "electronics"
        elif any(x in item_lower for x in ["bag", "backpack", "wallet", "purse"]):
            return "personal"
        elif any(x in item_lower for x in ["key", "umbrella", "glasses"]):
            return "accessories"
        elif any(x in item_lower for x in ["jacket", "coat", "hat", "clothing"]):
            return "clothing"
        elif any(x in item_lower for x in ["swim", "sport", "ball", "racket"]):
            return "sports"
        return "other"
    
    def get_spatial_temporal_stats(self) -> Dict:
        """Get combined stats from graph and spatial-temporal validator."""
        try:
            from src.intelligence.spatial_temporal_validator import get_spatial_temporal_validator
            stv = get_spatial_temporal_validator()
            stv_stats = stv.get_learning_stats()
        except Exception:
            stv_stats = {"error": "Spatial-temporal validator not available"}
        
        graph_stats = self.get_relationship_mining_stats()
        
        return {
            "graph": graph_stats,
            "spatial_temporal": stv_stats
        }


# ------------------------------------------------------------------ #
# Singleton Pattern for Global Access
# ------------------------------------------------------------------ #
_graph_manager_instance = None

def get_knowledge_graph() -> GraphManager:
    """
    Get or create the global GraphManager instance (singleton pattern).
    
    Returns:
        GraphManager: The global knowledge graph manager instance
    """
    global _graph_manager_instance
    if _graph_manager_instance is None:
        _graph_manager_instance = GraphManager()
    return _graph_manager_instance

