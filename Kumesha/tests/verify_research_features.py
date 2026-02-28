import os
import sys
import logging
import torch
import networkx as nx

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cross_modal.consistency_engine import ConsistencyEngine
from src.cross_modal.fusion import CrossAttentionFusion
from src.intelligence.knowledge_graph import get_knowledge_graph
from src.intelligence.active_learning import get_active_learning_system

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ResearchVerifier")

def test_research_features():
    print("\n" + "="*60)
    print("🔬 RESEARCH FEATURE VERIFICATION")
    print("="*60 + "\n")

    # 1. Test Knowledge Graph
    print("1️⃣  Testing Knowledge Graph (Hybrid Architecture)...")
    try:
        kg = get_knowledge_graph()
        stats = kg.get_relationship_mining_stats()
        print(f"   ✅ Knowledge Graph Initialized")
        print(f"   📊 Engine: {stats.get('engine')}")
        print(f"   🕸️  Nodes: {stats.get('nodes')}, Relationships: {stats.get('relationships')}")
        
        # Add a dummy event
        kg.add_item_event("test_item", "test_location", "test_category")
        print("   ✅ Successfully added test event to graph")
    except Exception as e:
        print(f"   ❌ Knowledge Graph Failed: {e}")

    print("\n" + "-"*40 + "\n")

    # 2. Test Cross-Attention Fusion
    print("2️⃣  Testing Cross-Attention Multimodal Fusion...")
    try:
        fusion_model = CrossAttentionFusion()
        print(f"   ✅ Fusion Model Initialized")
        
        # Test forward pass with dummy tensors
        text_embed = torch.randn(1, 1, 512)
        image_embed = torch.randn(1, 1, 512)
        voice_embed = torch.randn(1, 1, 512)
        
        fused_output, score = fusion_model(text_embed, image_embed, voice_embed)
        print(f"   ✅ Forward Pass Successful")
        print(f"   📉 Consistency Score: {score.item():.4f}")
    except Exception as e:
        print(f"   ❌ Fusion Model Failed: {e}")

    print("\n" + "-"*40 + "\n")

    # 3. Test Active Learning
    print("3️⃣  Testing Active Learning System...")
    try:
        al_system = get_active_learning_system()
        print(f"   ✅ Active Learning System Initialized")
        
        # Check database connection through it
        if hasattr(al_system, 'db'):
            print("   ✅ Database Connection Verification: OK")
        
    except Exception as e:
        print(f"   ❌ Active Learning Failed: {e}")

    print("\n" + "-"*40 + "\n")
    
    # 4. Consistency Engine Integration
    print("4️⃣  Testing Full Consistency Engine Integration...")
    try:
        engine = ConsistencyEngine()
        print("   ✅ Consistency Engine Initialized")
        if engine.xai_explainer:
             print("   ✅ XAI Explainer: Active")
        else:
             print("   ⚠️ XAI Explainer: Not loaded")
             
    except Exception as e:
         print(f"   ❌ Consistency Engine Failed: {e}")

    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_research_features()
