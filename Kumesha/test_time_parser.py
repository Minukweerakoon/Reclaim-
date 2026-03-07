#!/usr/bin/env python3
"""Quick test for time parser"""
import sys
sys.path.insert(0, '.')

from src.database.supabase_client import _parse_time_for_db

test_cases = [
    "2pm",
    "2:30pm",
    "14:00",
    "morning",
    "evening",
    "yesterday evening",
    "3 pm",
    "11:45 AM",
    "",
    None
]

print("Testing time parser:")
print("=" * 50)
for test in test_cases:
    result = _parse_time_for_db(test)
    print(f"Input: '{test}' → Output: '{result}'")
