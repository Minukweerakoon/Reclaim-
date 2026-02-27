"""Verify data in Supabase after E2E test."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from src.database.supabase_client import get_supabase_manager

sb = get_supabase_manager()

print("=" * 70)
print("LOST_ITEMS TABLE")
print("=" * 70)
lost = sb.get_lost_items(limit=20)
for r in lost:
    print(f"  ID:    {r['id'][:12]}...")
    print(f"  Email: {r.get('user_email','')}")
    print(f"  Type:  {r.get('item_type','')}")
    print(f"  Desc:  {r.get('description','')[:80]}")
    print(f"  Color: {r.get('color','')} | Brand: {r.get('brand','')}")
    print(f"  Loc:   {r.get('location','')}")
    print(f"  Score: {r.get('confidence_score','')} | Routing: {r.get('routing','')}")
    vs = r.get('validation_summary', {})
    if vs:
        print(f"  Val:   inputs={vs.get('input_types','?')} clip={vs.get('confidence',{}).get('cross_modal_scores',{}).get('clip_similarity','?')}")
    print()

print("=" * 70)
print("FOUND_ITEMS TABLE")
print("=" * 70)
found = sb.get_found_items(limit=20)
for r in found:
    print(f"  ID:    {r['id'][:12]}...")
    print(f"  Email: {r.get('user_email','')}")
    print(f"  Type:  {r.get('item_type','')}")
    print(f"  Desc:  {r.get('description','')[:80]}")
    print(f"  Color: {r.get('color','')} | Brand: {r.get('brand','')}")
    print(f"  Loc:   {r.get('location','')}")
    print(f"  Score: {r.get('confidence_score','')} | Routing: {r.get('routing','')}")
    vs = r.get('validation_summary', {})
    if vs:
        print(f"  Val:   inputs={vs.get('input_types','?')} clip={vs.get('confidence',{}).get('cross_modal_scores',{}).get('clip_similarity','?')}")
    print()

print(f"TOTALS: {len(lost)} lost items, {len(found)} found items")
